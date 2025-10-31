from __future__ import annotations
import numpy as np
import pandas as pd
import requests
from pathlib import Path
import yaml

def _load_api_keys():
    try:
        with open(Path("config/api_keys.yaml"), "r") as f:
            return yaml.safe_load(f).get("api_keys", {})
    except Exception:
        return {}

API_KEYS = _load_api_keys()

def _safe_get_json(url: str, params: dict | None = None, timeout: int = 10):
    try:
        r = requests.get(url, params=params or {}, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def get_fear_greed(index: pd.DatetimeIndex, mode: str = "live") -> pd.Series:
    if mode == "live":
        data = _safe_get_json("https://api.alternative.me/fng/", params={"limit": 0})
        if data and "data" in data:
            rows = data["data"]
            df = pd.DataFrame(rows)
            if "timestamp" in df.columns and "value" in df.columns:
                df["ts"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
                df = df.set_index("ts").sort_index()
                s = ((100 - df["value"].astype(float)) / 50.0) - 1.0  # 0=>+1, 50=>0, 100=>-1
                s = s.clip(-1, 1)
                out = s.reindex(index, method="ffill")
                return out.ffill().bfill().clip(-1, 1)
    n = len(index)
    t = np.arange(n)
    sim = 0.6 * np.sin(t / 48.0) + 0.15 * np.cos(t / 111.0) + np.random.default_rng(42).normal(0, 0.05, n)
    return pd.Series(np.clip(sim, -1, 1), index=index)

def get_funding_sentiment(symbol: str, index: pd.DatetimeIndex, mode: str = "live") -> pd.Series:
    def norm_rate(x: float) -> float:
        import numpy as _np
        return float(_np.tanh(-100.0 * x))
    if mode == "live":
        sym = symbol.replace("/", "")
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        try:
            js = requests.get(url, params={"symbol": sym, "limit": 1000}, timeout=10).json()
        except Exception:
            js = None
        if js:
            df = pd.DataFrame(js)
            if not df.empty and "fundingRate" in df.columns and "fundingTime" in df.columns:
                df["ts"] = pd.to_datetime(df["fundingTime"].astype(int), unit="ms")
                df = df.set_index("ts").sort_index()
                rates = df["fundingRate"].astype(float)
                s = rates.apply(norm_rate)
                return s.reindex(index, method="ffill").ffill().bfill().clip(-1, 1)
    rng = np.random.default_rng(123)
    n = len(index)
    steps = rng.normal(0, 0.00003, n).cumsum()
    rates = np.clip(steps, -0.0005, 0.0005)
    s = np.tanh(-100.0 * rates)
    return pd.Series(s, index=index).clip(-1, 1)

def get_news_sentiment(index: pd.DatetimeIndex, mode: str = "live") -> pd.Series:
    token = API_KEYS.get("cryptopanic", "")
    if mode == "live" and token:
        url = "https://cryptopanic.com/api/developer/v2/posts/"
        try:
            js = requests.get(url, params={"auth_token": token, "public": "true", "filter": "important"}, timeout=10).json()
        except Exception:
            js = None
        if js and "results" in js:
            rows = js["results"]
            scores = {}
            for r in rows:
                ts = pd.to_datetime(r.get("published_at") or r.get("created_at"))
                if ts is None:
                    continue
                k = ts.normalize()
                tags = r.get("votes", {})
                bull = (tags.get("positive", 0) or 0) + (1 if "bullish" in (r.get("tags") or []) else 0)
                bear = (tags.get("negative", 0) or 0) + (1 if "bearish" in (r.get("tags") or []) else 0)
                tot = bull + bear + 1e-9
                sc = (bull - bear) / tot
                scores[k] = scores.get(k, 0.0) + sc
            if scores:
                s = pd.Series(scores).sort_index().rolling(3, min_periods=1).mean().clip(-1, 1)
                if getattr(index, "tz", None) is not None:
                    index = index.tz_localize(None)
                if getattr(s.index, "tz", None) is not None:
                    s.index = s.index.tz_localize(None)
                return s.reindex(index, method="ffill").ffill().bfill().clip(-1, 1)
    n = len(index)
    t = np.arange(n)
    sim = 0.2 * np.sin(t / 64.0) + 0.1 * np.cos(t / 37.0)
    return pd.Series(np.clip(sim, -1, 1), index=index)

def get_combined_sentiment(symbol: str, index: pd.DatetimeIndex, mode: str = "live") -> pd.Series:
    fg = get_fear_greed(index, mode)
    fd = get_funding_sentiment(symbol, index, mode)
    nw = get_news_sentiment(index, mode)
    combo = pd.concat([fg, fd, nw], axis=1).fillna(0.0)
    combo.columns = ["fear_greed","funding","news"]
    out = combo.mean(axis=1).clip(-1, 1)
    return out.ewm(span=10, adjust=False).mean().clip(-1, 1)
