import yaml
from pathlib import Path
import pandas as pd

from src.adapters.exchange_ccxt import CCXTClient
from src.adapters.sentiment_providers import get_combined_sentiment
from src.indicators.trend import ema, supertrend
from src.indicators.momentum import rsi, macd
from src.indicators.volatility import atr
from src.signals.confluence import ConfluenceEngine, Weights, Thresholds
from src.signals.risk import RiskModel
from src.backtest.engine_sl_tp import bt_long_sl_tp
from src.utils.logging import setup_logging
from src.utils.mtf import align_to_lower_tf

log = setup_logging()

def load_yaml(path: Path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def tech_subscore(df: pd.DataFrame, cfg: dict) -> pd.Series:
    e20, e50, e200 = [ema(df['close'], w) for w in cfg['features']['ema']['windows']]
    r = rsi(df['close'], cfg['features']['rsi']['period'])
    macd_line, macd_sig, macd_hist = macd(df['close'], **cfg['features']['macd'])
    st = supertrend(df, **cfg['features']['supertrend'])

    score = pd.Series(0.0, index=df.index)
    score += (df['close'] > e200).astype(float) * 1.0 + (df['close'] <= e200).astype(float) * -1.0
    score += (e20 > e50).astype(float) * 0.5 + (e20 <= e50).astype(float) * -0.5
    score += (r > 55).astype(float) * 0.25 + (r < 45).astype(float) * -0.25
    score += ((macd_line > macd_sig) & (macd_hist > macd_hist.shift())).astype(float) * 0.25           + ((macd_line < macd_sig) & (macd_hist < macd_hist.shift())).astype(float) * -0.25
    score += (df['close'] > st).astype(float) * 0.25 + (df['close'] <= st).astype(float) * -0.25

    score = score / 2.25
    return score.clip(-1, 1)

def main():
    cfg = load_yaml(Path("config/settings.yaml"))
    api_mode = cfg.get("api_mode", "offline")

    engine = ConfluenceEngine(Weights(**cfg['confluence']['weights']), Thresholds(**cfg['confluence']['thresholds']))

    cc = CCXTClient(cfg['exchange'], market_type=cfg['market_type'])
    symbol = cfg['symbols'][0]

    tf_entry = cfg['timeframes'][0]
    tf_mid = "4h"
    tf_high = "1d"

    log.info(f"Fetching OHLCV for {symbol} [{tf_high}, {tf_mid}, {tf_entry}]...")
    df_high = cc.fetch_ohlcv_df(symbol, tf_high, lookback_bars=max(400, cfg['lookback_bars']//24))
    df_mid  = cc.fetch_ohlcv_df(symbol, tf_mid,  lookback_bars=max(800, cfg['lookback_bars']//6))
    df_low  = cc.fetch_ohlcv_df(symbol, tf_entry, lookback_bars=cfg['lookback_bars'])
    for df in (df_high, df_mid, df_low):
        df.columns = ['open','high','low','close','volume']

    log.info("Building indicators across timeframes...")
    tech_high = tech_subscore(df_high, cfg)
    tech_mid  = tech_subscore(df_mid, cfg)
    tech_low  = tech_subscore(df_low, cfg)

    log.info(f"[{api_mode.upper()}] Getting sentiment series...")
    sent_entry = get_combined_sentiment(symbol, df_low.index, api_mode)

    sentiment_weight_factor = 0.5 if api_mode == "offline" else 1.0

    total_high = (tech_high * engine.w.trend) + (sent_entry.reindex(df_high.index, method='ffill') * engine.w.sentiment_macro * sentiment_weight_factor)
    total_mid  = (tech_mid  * engine.w.trend) + (sent_entry.reindex(df_mid.index,  method='ffill') * engine.w.sentiment_macro * sentiment_weight_factor)
    total_low  = (tech_low  * engine.w.trend) + (sent_entry * engine.w.sentiment_macro * sentiment_weight_factor)

    total_high_on_low = align_to_lower_tf(total_high, df_low.index)
    total_mid_on_low  = align_to_lower_tf(total_mid,  df_low.index)

    decision_low = total_low.apply(engine.decide)

    gated = pd.Series("HOLD", index=df_low.index, dtype=object)
    buy_mask  = (decision_low == "BUY")  & (total_high_on_low >= 0) & (total_mid_on_low >= 0)
    sell_mask = (decision_low == "SELL") & (total_high_on_low <= 0) & (total_mid_on_low <= 0)
    gated[buy_mask] = "BUY"
    gated[sell_mask] = "SELL"

    atr_series = atr(df_low, cfg['features']['atr']['period'])

    entries = (gated == "BUY")
    exits   = (gated == "SELL")

    n_buy = int(entries.sum())
    n_sell = int(exits.sum())
    log.info(f"<green>BUY signals:</green> {n_buy} | <red>SELL signals:</red> {n_sell} | <blue>HOLD bars:</blue> {len(df_low) - n_buy - n_sell}")

    rm = RiskModel(**cfg['risk'])
    log.info("Running backtest with ATR SL/TP and position sizing...")
    curve = bt_long_sl_tp(df_low, entries, exits, atr_series, rm,
                          cfg['backtest']['fees_bps'],
                          cfg['backtest']['slippage_bps'],
                          cfg['backtest']['initial_equity'])

    start_equity = cfg['backtest']['initial_equity']
    end_equity = float(curve['equity'].iloc[-1])
    ret = (end_equity / start_equity - 1) * 100.0

    if end_equity >= start_equity:
        log.info(f"<green>End Equity: {end_equity:,.2f}  (Return: {ret:.2f}%)</green>")
    else:
        log.info(f"<red>End Equity: {end_equity:,.2f}  (Return: {ret:.2f}%)</red>")

    out_dir = Path("data/features")
    out_dir.mkdir(parents=True, exist_ok=True)
    curve.to_csv(out_dir / f"equity_curve_{symbol.replace('/','-')}_{tf_entry}_MTF_SLTP.csv")
    total_low.to_csv(out_dir / f"total_score_{symbol.replace('/','-')}_{tf_entry}_with_sentiment.csv")
    gated.to_csv(out_dir / f"gated_decisions_{symbol.replace('/','-')}_{tf_entry}.csv")

if __name__ == "__main__":
    main()
