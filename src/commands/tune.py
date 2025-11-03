from commands.base import BaseCommand
from analytics.threshold_tuner import scan_thresholds


class Command(BaseCommand):
    """Run threshold tuning across multiple buy/sell values."""

    def add_arguments(self, parser):
        parser.add_argument("--buy", nargs="+", type=float, default=[0.2, 0.3, 0.4, 0.5])
        parser.add_argument("--sell", nargs="+", type=float, default=[-0.2, -0.3, -0.4, -0.5])

    def handle(self, buy, sell, **kwargs):
        print(f"Running threshold scan for {buy=} {sell=}...")
        scan_thresholds(buy, sell)
        print("Threshold tuning completed.")
