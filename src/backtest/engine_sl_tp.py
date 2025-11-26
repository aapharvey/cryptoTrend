import pandas as pd


def bt_long_sl_tp(df: pd.DataFrame, entries: pd.Series, exits: pd.Series, atr_series: pd.Series,
                  risk_model, fees_bps: int = 7, slippage_bps: int = 5,
                  initial_equity: float = 10_000.0):
    price = df['close']
    high = df['high']
    low = df['low']
    open_ = df.get('open', price)

    fee_rate = (fees_bps + slippage_bps) / 10_000

    cash = initial_equity
    position_qty = 0.0
    entry_price = None
    entry_time = None
    sl = None
    tp = None
    active_trade = None

    curve = []
    trades: list[dict] = []

    for ts in df.index:
        mark_price = price.loc[ts]
        equity = cash + position_qty * mark_price

        if position_qty > 0:
            hit_sl = (low.loc[ts] <= sl) if sl is not None else False
            hit_tp = (high.loc[ts] >= tp) if tp is not None else False
            exit_px = None
            exit_reason = None
            if hit_sl and hit_tp:
                bar_open = open_.loc[ts]
                dist_sl = max(bar_open - sl, 0.0)
                dist_tp = max(tp - bar_open, 0.0)
                if dist_sl <= dist_tp:
                    exit_px = sl
                    exit_reason = "stop_loss"
                else:
                    exit_px = tp
                    exit_reason = "take_profit"
            elif hit_sl:
                exit_px = sl
                exit_reason = "stop_loss"
            elif hit_tp:
                exit_px = tp
                exit_reason = "take_profit"
            elif bool(exits.get(ts, False)):
                exit_px = mark_price
                exit_reason = "signal_exit"

            if exit_px is not None:
                gross_proceeds = position_qty * exit_px
                exit_fee = gross_proceeds * fee_rate
                cash += gross_proceeds - exit_fee
                realized_pnl = gross_proceeds - exit_fee - active_trade["entry_cost"]
                active_trade.update({
                    "exit_time": ts,
                    "exit_price": float(exit_px),
                    "exit_fee": float(exit_fee),
                    "pnl": float(realized_pnl),
                    "pnl_pct": float(realized_pnl / active_trade["equity_at_entry"]),
                    "return_on_risk": float(
                        realized_pnl / max(active_trade["capital_risked"], 1e-9)
                    ),
                    "holding_period": ts - active_trade["entry_time"],
                    "exit_reason": exit_reason,
                })
                trades.append(active_trade)

                position_qty = 0.0
                entry_price = None
                entry_time = None
                sl = None
                tp = None
                active_trade = None
                equity = cash

        if position_qty == 0 and bool(entries.get(ts, False)):
            entry_price = mark_price
            atr_val = float(atr_series.loc[ts])
            legs = risk_model.construct(equity, entry_price, atr_val, "LONG")
            sl, tp = legs["sl"], legs["tp"]
            qty = max(0.0, float(legs.get("qty", 0.0)))
            if qty <= 0:
                continue
            max_affordable_qty = (
                cash / (entry_price * (1 + fee_rate)) if entry_price > 0 else 0.0
            )
            if max_affordable_qty > 0 and qty > max_affordable_qty:
                qty = max_affordable_qty
            gross_cost = qty * entry_price
            entry_fee = gross_cost * fee_rate
            total_cost = gross_cost + entry_fee
            if total_cost > cash or qty <= 0:
                continue
            cash -= total_cost
            position_qty = qty
            entry_time = ts
            active_trade = {
                "entry_time": ts,
                "entry_price": float(entry_price),
                "qty": float(qty),
                "entry_fee": float(entry_fee),
                "stop_loss": float(sl),
                "take_profit": float(tp),
                "capital_risked": float(abs(entry_price - sl) * qty),
                "entry_cost": float(total_cost),
                "equity_at_entry": float(equity),
            }

        equity = cash + position_qty * mark_price
        curve.append((ts, equity))

    curve_df = pd.DataFrame(curve, columns=['timestamp', 'equity']).set_index('timestamp')
    return curve_df, trades
