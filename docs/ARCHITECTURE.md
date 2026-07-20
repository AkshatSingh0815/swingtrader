# Swing Trading Platform — Architecture

## 1. Goal
Every evening after NSE close, scan the full NSE universe, compute technical
indicators, detect candlestick/chart patterns, score every stock, generate
buy/sell signals with risk management, blend in news sentiment, and surface
a ranked dashboard + alerts. Nightly job runs via GitHub Actions (no PC needed).

## 2. High-level flow

```
GitHub Actions (cron, 6:30 PM IST weekdays)
        │
        ▼
scanner/scan_runner.py  (orchestrator)
        │
        ├─ services/nse_symbols.py      → get full NSE symbol list
        ├─ services/data_fetcher.py     → yfinance OHLCV, batched, retried
        ├─ scanner/indicators.py        → RSI, MACD, EMA/SMA, VWAP, ATR, ADX,
        │                                  SuperTrend, BBands, StochRSI, OBV,
        │                                  MFI, CCI, Ichimoku
        ├─ scanner/candlestick_patterns.py → 11 candlestick patterns
        ├─ scanner/chart_patterns.py     → 11 chart/breakout patterns (rule-based)
        ├─ news/news_fetcher.py + sentiment.py → NewsAPI + VADER/FinBERT-lite
        ├─ machine_learning/predict.py   → P(move ≥5/10/15/20% in 5/10/20d)
        ├─ scanner/scoring.py            → weighted composite score (0-100)
        ├─ signals/signal_engine.py      → BUY/SELL/HOLD + reasons
        ├─ signals/risk_management.py    → entry/SL/T1-3/position size/RR
        ├─ database/db.py                → persist everything to SQLite
        └─ services/alerts.py            → Telegram/email on Strong Buy etc.
        │
        ▼
SQLite (swingtrader.db)
        │
   ┌────┴─────┐
   ▼          ▼
FastAPI    Streamlit
(backend)  (frontend, reads via FastAPI or DB directly)
        │
        ▼
   You, every morning
```

## 3. Why this shape (given real-world constraints)
- **No always-on server required.** GitHub Actions runs the scan on a
  schedule and commits the resulting SQLite DB (or pushes to a small
  hosted Postgres/SQLite endpoint) — free tier is enough for a daily batch job.
- **FastAPI + Streamlit are decoupled.** FastAPI exposes read APIs over the
  DB; Streamlit is a thin client. You can deploy FastAPI on Render/Railway
  and run Streamlit locally or also on Render.
- **Rule-based chart pattern detection**, not vision/ML pattern recognition.
  This is the realistic, explainable, and maintainable approach without a
  large labeled chart-image dataset — and it's what most retail-grade
  scanners actually use under the hood.
- **ML layer is a probability model**, not a price predictor. It outputs
  calibrated probabilities of hitting move thresholds — framed honestly as
  ranking/risk input, not a prophecy.

## 4. Database schema (SQLAlchemy models)

**stocks** — symbol, name, sector, industry, is_active
**price_history** — symbol, date, OHLCV (cached to avoid re-fetching)
**indicators** — symbol, date, all computed indicator values (wide table)
**patterns** — symbol, date, pattern_name, pattern_type(candlestick/chart), direction
**scores** — symbol, date, technical_score, momentum_score, volume_score,
  news_score, fundamental_score, overall_score, rank
**signals** — symbol, date, signal_type(BUY/SELL/HOLD), entry, stop_loss,
  target1/2/3, position_size, risk_pct, rr_ratio, expected_return, reasons(json)
**news_sentiment** — symbol, date, headline, sentiment, score, source
**ml_predictions** — symbol, date, horizon_days, threshold_pct, probability
**backtest_results** — strategy_name, run_date, win_rate, avg_profit,
  avg_loss, sharpe, max_drawdown, annual_return
**watchlist** — symbol, added_date, notes
**portfolio** — symbol, qty, buy_price, buy_date, current_price (refreshed)

## 5. API design (FastAPI, prefix `/api/v1`)

```
GET  /stocks                       list/search stocks
GET  /stocks/{symbol}              detail + latest indicators
GET  /stocks/{symbol}/history      OHLCV for charting
GET  /scans/latest                 latest full scan results (paginated, filterable)
GET  /scans/top/{category}         swing|breakout|momentum|penny|dividend|
                                    railway|banking|defence|renewable
GET  /signals/latest               today's BUY/SELL signals
GET  /signals/{symbol}             signal history for a stock
GET  /heatmap/{index}              nifty|banknifty sector heatmap data
GET  /watchlist                    | POST | DELETE
GET  /portfolio                    | POST | DELETE
GET  /backtest/{strategy}          backtest metrics
POST /chat                         AI assistant Q&A over the day's scan
GET  /reports/daily.pdf            generated PDF report
GET  /reports/weekly.xlsx          generated Excel report
```

## 6. Scoring model (0–100)
`overall = 0.40*technical + 0.25*momentum + 0.15*volume + 0.10*news + 0.10*fundamentals`
Each sub-score is itself a weighted blend documented in `scanner/scoring.py`.

## 7. Roadmap (build order used in this project)
1. Config, logging, DB models
2. Symbol universe + data fetcher (with local OHLCV cache)
3. Indicators
4. Candlestick + chart pattern detectors
5. News fetch + sentiment
6. ML feature engineering + probability model + training script
7. Scoring engine
8. Signal engine + risk management
9. Backtesting engine
10. Scan orchestrator (ties 1–9 together, writes DB)
11. Alerts (Telegram/email)
12. FastAPI backend
13. Streamlit frontend
14. Reports (PDF/Excel), AI chat assistant
15. Tests, Docker, docker-compose, GitHub Actions, docs
