import pandas as pd


def generate_trade_log(df_prices: pd.DataFrame, entries: pd.Series, exits: pd.Series):
    trades = []
    in_trade = False
    entry_px = None
    entry_time = None

    prices = df_prices['close']

    for ts in df_prices.index:
        if not in_trade and bool(entries.get(ts, False)):
            in_trade = True
            entry_time = ts
            entry_px = float(prices.loc[ts])
        elif in_trade and bool(exits.get(ts, False)):
            exit_px = float(prices.loc[ts])
            pnl = (exit_px - entry_px) / entry_px
            trades.append({
                "entry_time": entry_time,
                "exit_time": ts,
                "entry": entry_px,
                "exit": exit_px,
                "pnl": float(pnl),
                "holding_bars": (ts - entry_time),
            })
            in_trade = False
            entry_px = None
            entry_time = None

    return pd.DataFrame(trades)
