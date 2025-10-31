import pandas as pd

def bt_long_sl_tp(df: pd.DataFrame, entries: pd.Series, exits: pd.Series, atr_series: pd.Series,
                  risk_model, fees_bps: int = 7, slippage_bps: int = 5, initial_equity: float = 10_000.0):
    price = df['close']
    high = df['high']
    low = df['low']

    equity = initial_equity
    position = 0.0
    entry_price = None
    sl = None
    tp = None

    curve = []

    fee_mult_buy = 1 - (fees_bps + slippage_bps) / 10_000
    fee_mult_sell = 1 - (fees_bps + slippage_bps) / 10_000

    for ts in df.index:
        if position > 0:
            hit_sl = (low.loc[ts] <= sl) if sl is not None else False
            hit_tp = (high.loc[ts] >= tp) if tp is not None else False
            exit_px = None
            if hit_sl and hit_tp:
                exit_px = sl
            elif hit_sl:
                exit_px = sl
            elif hit_tp:
                exit_px = tp
            elif bool(exits.get(ts, False)):
                exit_px = price.loc[ts]

            if exit_px is not None:
                equity = position * exit_px * fee_mult_sell
                position = 0.0
                entry_price = None
                sl = None
                tp = None

        if position == 0 and bool(entries.get(ts, False)):
            entry_price = price.loc[ts]
            atr_val = float(atr_series.loc[ts])
            legs = risk_model.construct(equity, entry_price, atr_val, "LONG")
            sl, tp = legs["sl"], legs["tp"]
            qty = legs["qty"]
            position = qty * fee_mult_buy

        curve.append((ts, equity if position == 0 else position * price.loc[ts]))

    return pd.DataFrame(curve, columns=['timestamp','equity']).set_index('timestamp')
