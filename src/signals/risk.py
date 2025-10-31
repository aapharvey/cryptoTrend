class RiskModel:
    def __init__(self, risk_per_trade: float = 0.01, sl_atr_mult: float = 2.0, tp_rr: float = 2.0):
        self.rpt = risk_per_trade
        self.slm = sl_atr_mult
        self.rr = tp_rr

    def construct(self, equity: float, entry: float, atr: float, direction: str):
        direction = direction.upper()
        if direction == "LONG":
            sl = entry - atr * self.slm
            tp = entry + (entry - sl) * self.rr
        else:
            sl = entry + atr * self.slm
            tp = entry - (sl - entry) * self.rr
        risk_per_unit = abs(entry - sl)
        qty = (equity * self.rpt) / risk_per_unit if risk_per_unit > 0 else 0.0
        return {"sl": sl, "tp": tp, "qty": qty}
