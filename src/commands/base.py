import argparse


class BaseCommand:
    """Base class for all CryptoTrend commands."""

    def get_parser(self):
        return argparse.ArgumentParser(description=self.__doc__)

    def run(self, args):
        parser = self.get_parser()
        self.add_arguments(parser)
        opts = parser.parse_args(args)
        self.handle(**vars(opts))

    def add_arguments(self, parser):
        """Override to define custom arguments."""
        pass

    def handle(self, **options):
        """Override to implement command logic."""
        raise NotImplementedError("Subclasses must implement handle()")
