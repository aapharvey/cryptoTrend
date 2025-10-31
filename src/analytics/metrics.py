import pandas as pd
import numpy as np

def compute_returns(equity_curve: pd.Series) -> pd.Series:
    return equity_curve.pct_change().dropna()

def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 365*24):
    if returns.empty or returns.std(ddof=0) == 0:
        return 0.0
    excess = returns - risk_free_rate/periods_per_year
    return float(np.sqrt(periods_per_year) * excess.mean() / (excess.std(ddof=0) + 1e-12))

def max_drawdown(equity_curve: pd.Series):
    roll_max = equity_curve.cummax()
    drawdown = equity_curve / roll_max - 1.0
    return float(drawdown.min()), drawdown

def total_return(equity_curve: pd.Series):
    if len(equity_curve) < 2:
        return 0.0
    return float((equity_curve.iloc[-1] / equity_curve.iloc[0] - 1.0) * 100.0)

def win_rate(trades_df: pd.DataFrame):
    if trades_df is None or trades_df.empty:
        return 0.0
    wins = (trades_df['pnl'] > 0).sum()
    return float(wins / len(trades_df))

def profit_factor(trades_df: pd.DataFrame):
    if trades_df is None or trades_df.empty:
        return 0.0
    gains = trades_df.loc[trades_df['pnl'] > 0, 'pnl'].sum()
    losses = -trades_df.loc[trades_df['pnl'] < 0, 'pnl'].sum()
    return float(gains / losses) if losses > 0 else float('inf')

def summary(curve_df: pd.DataFrame, trades_df: pd.DataFrame, start_equity: float):
    eq = curve_df['equity']
    rets = compute_returns(eq)
    sharpe = sharpe_ratio(rets)
    mdd, dd_series = max_drawdown(eq)
    wr = win_rate(trades_df)
    pf = profit_factor(trades_df)
    tret = total_return(eq)
    out = {
        "start_equity": float(start_equity),
        "end_equity": float(eq.iloc[-1]),
        "total_return": float(tret),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(mdd*100.0),
        "win_rate": float(wr*100.0),
        "profit_factor": float(pf),
        "num_trades": int(0 if trades_df is None else len(trades_df)),
        "drawdown_series": dd_series,
    }
    return out
