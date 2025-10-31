import yaml
from pathlib import Path
import pandas as pd

from src.adapters.exchange_ccxt import CCXTClient
from src.indicators.trend import ema, supertrend
from src.indicators.momentum import rsi, macd
from src.indicators.volatility import atr
from src.signals.confluence import ConfluenceEngine, Weights, Thresholds
from src.backtest.engine_naive import naive_long_only_bt
from src.utils.logging import setup_logging

log = setup_logging()

def load_yaml(path: Path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def tech_subscore(df: pd.DataFrame, cfg: dict) -> pd.Series:
    e20, e50, e200 = [ema(df['close'], w) for w in cfg['features']['ema']['windows']]
    r = rsi(df['close'], cfg['features']['rsi']['period'])
    macd_line, macd_sig, macd_hist = macd(df['close'], **cfg['features']['macd'])
    st = supertrend(df, **cfg['features']['supertrend'])

    # Normalize per-bar technical score into [-1, 1]
    score = pd.Series(0.0, index=df.index)
    score += (df['close'] > e200).astype(float) * 1.0 + (df['close'] <= e200).astype(float) * -1.0
    score += (e20 > e50).astype(float) * 0.5 + (e20 <= e50).astype(float) * -0.5
    score += (r > 55).astype(float) * 0.25 + (r < 45).astype(float) * -0.25
    score += ((macd_line > macd_sig) & (macd_hist > macd_hist.shift())).astype(float) * 0.25           + ((macd_line < macd_sig) & (macd_hist < macd_hist.shift())).astype(float) * -0.25
    score += (df['close'] > st).astype(float) * 0.25 + (df['close'] <= st).astype(float) * -0.25

    # Scale to [-1, 1] by dividing by max possible (1+0.5+0.25+0.25+0.25=2.25)
    score = score / 2.25
    return score.clip(-1, 1)

def main():
    cfg = load_yaml(Path("config/settings.yaml"))
    cc = CCXTClient(cfg['exchange'], market_type=cfg['market_type'])

    symbol = cfg['symbols'][0]
    tf = cfg['timeframes'][0]

    log.info(f"Fetching OHLCV for {symbol} {tf} ...\n")
    df = cc.fetch_ohlcv_df(symbol, tf, lookback_bars=cfg['lookback_bars'])
    df.columns = ['open','high','low','close','volume']

    log.info("Building indicators...\n")
    tech = tech_subscore(df, cfg)

    # Placeholders for on-chain & sentiment (0 = neutral). Pluggable later.
    onchain = pd.Series(0.0, index=df.index)
    sent = pd.Series(0.0, index=df.index)

    engine = ConfluenceEngine(Weights(**cfg['confluence']['weights']), Thresholds(**cfg['confluence']['thresholds']))

    total_score = tech * engine.w.trend + onchain * engine.w.onchain + sent * engine.w.sentiment_macro
    decision = total_score.apply(engine.decide)

    # Convert to naive entries/exits: go long on BUY, exit on SELL
    entries = (decision == "BUY")
    exits = (decision == "SELL")

    log.info("Running naive long-only backtest...\n")
    curve = naive_long_only_bt(df, entries, exits, cfg['backtest']['fees_bps'], cfg['backtest']['slippage_bps'], cfg['backtest']['initial_equity'])

    # Basic metrics
    start_equity = cfg['backtest']['initial_equity']
    end_equity = float(curve['equity'].iloc[-1])
    ret = (end_equity / start_equity - 1) * 100.0

    print("==== Backtest Summary ====")
    print(f"Symbol/TF: {symbol} {tf}")
    print(f"Start Equity: {start_equity:,.2f}")
    print(f"End Equity:   {end_equity:,.2f}")
    print(f"Return:       {ret:.2f}%")
    print(f"Bars:         {len(df)}")

    # Save outputs
    out_dir = Path("data/features")
    out_dir.mkdir(parents=True, exist_ok=True)
    curve.to_csv(out_dir / f"equity_curve_{symbol.replace('/','-')}_{tf}.csv")
    total_score.to_csv(out_dir / f"total_score_{symbol.replace('/','-')}_{tf}.csv")

if __name__ == "__main__":
    main()
