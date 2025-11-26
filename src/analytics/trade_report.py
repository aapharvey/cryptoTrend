import pandas as pd
from typing import Iterable


def generate_trade_log(trades: Iterable[dict] | pd.DataFrame | None) -> pd.DataFrame:
    """Normalise the trade records emitted by the backtest engine.

    The engine already accounts for position sizing, fees, and slippage. This helper simply
    converts its structured trade list into a DataFrame (or copies one if already provided)
    so the analytics stack downstream can consume consistent data.
    """

    if trades is None:
        return pd.DataFrame()

    if isinstance(trades, pd.DataFrame):
        df = trades.copy()
    else:
        df = pd.DataFrame(list(trades))

    if df.empty:
        return df

    numeric_cols = [
        "qty",
        "entry_fee",
        "exit_fee",
        "capital_risked",
        "entry_cost",
        "equity_at_entry",
        "pnl",
        "pnl_pct",
        "return_on_risk",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(float)

    column_order = [
        "entry_time",
        "exit_time",
        "entry_price",
        "exit_price",
        "qty",
        "stop_loss",
        "take_profit",
        "entry_fee",
        "exit_fee",
        "capital_risked",
        "entry_cost",
        "equity_at_entry",
        "pnl",
        "pnl_pct",
        "return_on_risk",
        "holding_period",
        "exit_reason",
    ]
    cols = [c for c in column_order if c in df.columns]
    return df.loc[:, cols + [c for c in df.columns if c not in cols]]
