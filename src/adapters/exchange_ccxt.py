import ccxt
import pandas as pd
from typing import Optional
from ..utils.timeframes import timeframe_to_ms

class CCXTClient:
    def __init__(self, exchange_name: str, api_key: Optional[str] = None, secret: Optional[str] = None, market_type: str = "spot"):
        ex_cls = getattr(ccxt, exchange_name)
        self.ex = ex_cls({
            "apiKey": api_key or "",
            "secret": secret or "",
            "enableRateLimit": True,
        })
        if exchange_name == "binance":
            if market_type.lower().startswith("future"):
                self.ex.options["defaultType"] = "future"
            else:
                self.ex.options["defaultType"] = "spot"

    def fetch_ohlcv_df(self, symbol: str, timeframe: str, since_ms: Optional[int] = None, limit: int = 1000, lookback_bars: int = 1500) -> pd.DataFrame:
        all_rows = []
        tf_ms = timeframe_to_ms(timeframe)
        if since_ms is None:
            now = self.ex.milliseconds()
            since_ms = now - (lookback_bars + 5) * tf_ms

        while True:
            batch = self.ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            if not batch:
                break
            all_rows += batch
            last_ts = batch[-1][0]
            since_ms = last_ts + 1
            if len(all_rows) >= lookback_bars:
                break

        if not all_rows:
            raise RuntimeError("No OHLCV data returned")
        df = pd.DataFrame(all_rows, columns=["timestamp","open","high","low","close","volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df
