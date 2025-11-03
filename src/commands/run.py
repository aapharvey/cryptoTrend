from commands.base import BaseCommand
from core.backtest_runner import run_strategy


class Command(BaseCommand):
    """Run a single backtest."""

    def add_arguments(self, parser):
        parser.add_argument("--symbol", default="BTC/USDT")
        parser.add_argument("--tf", default="1h")

    def handle(self, symbol, tf, **kwargs):
        print(f"Running backtest for {symbol} on {tf} timeframe...")
        run_strategy()
