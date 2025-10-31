import pandas as pd

def naive_long_only_bt(df: pd.DataFrame, entries: pd.Series, exits: pd.Series, fees_bps: int = 7, slippage_bps: int = 5, initial_equity: float = 10_000.0):
    price = df['close']
    equity = initial_equity
    position = 0.0
    entry_price = None
    curve = []

    fee_mult = 1 - fees_bps / 10_000 - slippage_bps / 10_000

    for ts in df.index:
        if position == 0 and bool(entries.get(ts, False)):
            entry_price = price.loc[ts]
            position = equity / entry_price * fee_mult
        elif position > 0 and bool(exits.get(ts, False)):
            equity = position * price.loc[ts] * fee_mult
            position = 0.0
            entry_price = None

        # mark-to-market
        if position > 0:
            curve.append((ts, position * price.loc[ts]))
        else:
            curve.append((ts, equity))

    out = pd.DataFrame(curve, columns=['timestamp','equity']).set_index('timestamp')
    return out
