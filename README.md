# NSE Swing Trading Platform

A personal, fully-automated swing-trading analysis platform for the Indian
stock market (NSE). Every weekday evening it scans stocks, computes
technical indicators, detects candlestick/chart patterns, blends in news
sentiment and an ML move-probability model, ranks everything into a
composite score, and produces BUY/SELL signals with a full risk-management
plan (entry, stop-loss, three targets, position sizing).

**This ranks and flags opportunities based on technical strength, momentum,
sentiment, and risk. It does not predict the future, and nothing here is
financial advice** — always size positions according to your own risk
tolerance and do your own due diligence.

## What it does

- 🔍 Scans the full NSE universe (or NIFTY50/500/your watchlist) after market close
- 📊 18 technical indicators: RSI, MACD, EMA 20/50/200, SMA, VWAP, ATR, ADX,
  SuperTrend, Bollinger Bands, Stochastic RSI, OBV, MFI, CCI, Ichimoku Cloud
- 🕯️ 12 candlestick patterns + 11 chart/breakout patterns (rule-based)
- 📰 News sentiment analysis (NewsAPI + VADER, finance-tuned lexicon)
- 🤖 ML probability model: P(stock moves ≥5/10/15/20% within 5/10/20 trading days)
- 🏆 Weighted composite score (0-100): Technical 40% / Momentum 25% / Volume
  15% / News 10% / Fundamentals 10%
- 💰 Full risk management: entry, ATR-based stop-loss, 3 targets, position
  sizing, risk:reward ratio
- 📈 Backtesting engine with win rate, Sharpe ratio, max drawdown, annual return
- 🔔 Telegram/email alerts on Strong Buy signals
- 📱 Streamlit dashboard: category tabs, market heatmap, stock charts,
  watchlist, portfolio tracker, AI chat assistant
- 🌐 FastAPI backend for programmatic access
- 📄 Daily PDF report + weekly Excel export
- ⏰ Fully automated via GitHub Actions (free) — no server or PC required to
  run daily

## Quick start (local)

```bash
git clone <your-repo-url>
cd swingtrader
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # fill in API keys (all optional except DB path)

# Initialize the DB and run your first scan (starts with NIFTY50 by default is
# recommended for a first run — see docs/INSTALL.md to switch to full NSE)
python -m scanner.scan_runner

# Start the API (in one terminal)
uvicorn backend.main:app --reload

# Start the dashboard (in another terminal)
streamlit run frontend/app.py
```

Open http://localhost:8501 for the dashboard, http://localhost:8000/docs for
the interactive API docs.

## Running it daily without your PC (GitHub Actions)

See `.github/workflows/daily_scan.yml` — it's pre-configured to run every
weekday at 18:30 IST, cache the SQLite DB between runs, and commit results
back to your repo. Add your API keys as repository secrets
(`Settings → Secrets and variables → Actions`):
`NEWSAPI_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SMTP_USER`,
`SMTP_PASSWORD`, `ALERT_EMAIL_TO`. None are required for the scan itself to
run — only for news sentiment and alerts.

## Docs

- `docs/ARCHITECTURE.md` — system design, schema, API design, roadmap
- `docs/INSTALL.md` — detailed installation & deployment guide
- `docs/API.md` — full API reference
- `docs/DEVELOPER_GUIDE.md` — code layout, how to extend

## Project layout

```
backend/        FastAPI app + routes
frontend/       Streamlit dashboard
database/       SQLAlchemy models + DB session
services/       Data fetching, NSE symbol universe, alerts
scanner/        Indicators, pattern detection, scoring, scan orchestrator
signals/        Buy/sell signal engine, risk management
strategies/     Ties everything into one per-stock evaluation
news/           News fetching + sentiment
machine_learning/  Feature engineering, training, prediction
backtesting/    Backtest engine
utils/          Config, logging
tests/          pytest test suite
docs/           Documentation
.github/workflows/  CI + scheduled daily scan
```

## Honest limitations (please read)

- **Chart pattern detection is rule-based**, not computer vision — it's
  explainable and fast, but will occasionally miss or misclassify patterns
  a trained eye would catch differently.
- **The ML model outputs probabilities, not predictions.** Train it on more
  history/symbols (`python -m machine_learning.train_model`) before trusting
  it; check the logged AUC per horizon/threshold.
- **NSE's official API can rate-limit or change** without notice; the
  symbol-universe fetcher falls back to a small bundled CSV so the pipeline
  never hard-fails, but you should refresh `data/nse_equity_list.csv`
  periodically for full-market coverage.
- **Backtests use simulated fills** (next-bar stop/target checks), not real
  slippage/liquidity — treat results directionally, not as guaranteed returns.
