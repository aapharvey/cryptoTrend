#!/usr/bin/env python3
"""
CryptoTrend Command Manager
Usage:
    python manage.py backtest
    python manage.py tune --buy 0.3 0.4 --sell -0.3 -0.4
    python manage.py dashboard
"""

import sys
from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))


def main():
    if len(sys.argv) < 2:
        print("Usage: python manage.py <command> [args]")
        sys.exit(1)

    command_name = sys.argv[1]
    try:
        module = importlib.import_module(f"commands.{command_name}")
    except ModuleNotFoundError:
        print(f"Unknown command: {command_name}")
        sys.exit(1)

    command = getattr(module, "Command", None)
    if not command:
        print(f"Command '{command_name}' missing Command class.")
        sys.exit(1)

    cmd = command()
    cmd.run(sys.argv[2:])


if __name__ == "__main__":
    main()
