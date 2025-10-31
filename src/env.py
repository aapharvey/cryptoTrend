from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env automatically at import
load_dotenv(dotenv_path=Path(".env"), override=True)

def get_env(key: str, default=None) -> str:
    """Fetch a variable from environment or return default."""
    return os.getenv(key, default)

def get_api_keys() -> dict:
    """Return all known API keys as a dictionary."""
    return {
        "cryptopanic": get_env("CRYPTOPANIC_API_KEY", ""),
        "glassnode": get_env("GLASSNODE_API_KEY", ""),
        "santiment": get_env("SANTIMENT_API_KEY", ""),
    }

# Common globals for convenience
API_MODE = get_env("API_MODE", "offline")
BINANCE_TYPE = get_env("BINANCE_TYPE", "futures")
