from dataclasses import dataclass

@dataclass
class Weights:
    trend: float = 0.40
    onchain: float = 0.35
    sentiment_macro: float = 0.25

@dataclass
class Thresholds:
    buy: float = 0.65
    sell: float = -0.65
    neutral_band: float = 0.20

class ConfluenceEngine:
    def __init__(self, weights: Weights, th: Thresholds):
        self.w = weights
        self.th = th

    def score(self, tech: float, onchain: float, sent: float) -> float:
        return tech * self.w.trend + onchain * self.w.onchain + sent * self.w.sentiment_macro

    def decide(self, total_score: float) -> str:
        if total_score >= self.th.buy:
            return "BUY"
        if total_score <= self.th.sell:
            return "SELL"
        if abs(total_score) < self.th.neutral_band:
            return "HOLD"
        return "WAIT"
