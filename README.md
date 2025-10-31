# Crypto Trend — Starter

A minimal scaffold to start implementing the confluence-based trend predictor (TA + On-chain + Sentiment).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_backtest.py
```

By default it fetches ~1500 1h bars for BTC/USDT on Binance (futures market mode), builds indicators, computes a technical-only confluence score, and runs a naive long-only backtest using BUY/SELL states.

## Structure
- `config/settings.yaml` — symbols, timeframes, indicator params, confluence weights, backtest settings
- `src/adapters/exchange_ccxt.py` — robust OHLCV fetcher with pagination
- `src/indicators/*` — EMA, RSI, MACD, ATR, SuperTrend
- `src/signals/confluence.py` — weighted scoring + decision logic
- `src/backtest/engine_naive.py` — simple long-only engine to validate signal shape
- `run_backtest.py` — ties everything together

## Next Steps
- Plug in **on-chain** and **sentiment** providers (return a normalized [-1,1] series)
- Replace naive backtester with vectorbt/backtrader for SL/TP and fees modeling
- Add multi-timeframe alignment (1D bias, 4H confirmation, 1H entries)
- Add risk model (ATR-based SL/TP, position sizing) and live executor
