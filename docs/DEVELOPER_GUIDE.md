# Developer Guide

## Code layout & where to extend things

| Want to... | Edit this |
|---|---|
| Add a new technical indicator | `scanner/indicators.py` (`compute_all_indicators`), then add a column to `database/models/indicator.py` |
| Add a candlestick pattern | `scanner/candlestick_patterns.py`: write a `is_xxx(df)` function, register it in `CANDLESTICK_PATTERNS` |
| Add a chart pattern | `scanner/chart_patterns.py`: extend `detect_chart_patterns` |
| Change scoring weights | `.env` (`WEIGHT_TECHNICAL`, etc.) or `utils/config.py` defaults |
| Change what makes a BUY/SELL signal | `signals/signal_engine.py` |
| Change stop-loss/target math or position sizing | `signals/risk_management.py` |
| Add a new dashboard category (e.g. "IT stocks") | `scanner/categorize.py` |
| Add a new data source (e.g. Finnhub fundamentals) | new file in `services/`, wire into `strategies/swing_strategy.py` |
| Add a REST endpoint | new file in `backend/api/`, register the router in `backend/main.py` |
| Add a dashboard page | `frontend/app.py` — add to the sidebar `page` radio list |
| Change the ML model / add features | `machine_learning/features.py` (`FEATURE_COLUMNS`), then retrain |

## Design decisions worth knowing before you extend this

1. **Everything flows through `strategies/swing_strategy.py::evaluate_stock`.**
   Both the live scanner (`scanner/scan_runner.py`) and the backtester
   (`backtesting/backtest_engine.py`) should call the same evaluation logic
   wherever possible, so backtest results actually reflect what the live
   scan would have done. (The backtester currently re-implements a
   lighter-weight version of the pipeline for speed — see the note in
   `backtest_engine.py` if you want to fully unify them.)

2. **Every external call degrades gracefully.** News fetch, NSE symbol
   fetch, alerts, and ML prediction all catch their own exceptions and
   return empty/neutral defaults rather than raising — so a scan of 2000
   stocks doesn't die because one API had a bad day. Keep this pattern when
   adding new data sources.

3. **No lookahead in training.** `machine_learning/features.py::build_labels`
   is only ever called during training, using future price data to label
   the past. `predict.py` only ever builds features from the *current* row.
   If you touch this file, keep that boundary intact.

4. **SQLite is fine for this scale** (a few thousand symbols × a few years
   of daily bars). If you outgrow it — e.g. you add intraday data — swap
   `DATABASE_URL` in `.env` for a Postgres URL; SQLAlchemy doesn't care.

## Running things individually

```bash
# Just the indicator/pattern/scoring pipeline on one stock, for debugging:
python -c "
from services.data_fetcher import fetch_history
from strategies.swing_strategy import evaluate_stock
df = fetch_history('TCS')
print(evaluate_stock('TCS', 'Tata Consultancy Services', df))
"

# Retrain ML models on a wider universe:
python -c "
from machine_learning.train_model import train_all
from services.nse_symbols import get_symbol_universe
train_all(get_symbol_universe('NIFTY500'))
"

# Run the backtester on one symbol:
python -c "
from services.data_fetcher import fetch_history
from backtesting.backtest_engine import backtest_symbol, compute_metrics
trades = backtest_symbol(fetch_history('TCS', period='5y'))
print(compute_metrics(trades))
"
```

## Testing

```bash
pytest tests/ -v
```

Tests use synthetic OHLCV data (no network calls), so they run fast and
deterministically in CI. When adding a new indicator/pattern/scoring rule,
add a corresponding unit test in `tests/`.

## Style

Type hints + docstrings on all public functions, PEP8 (no strict linter
wired in yet — add `ruff` or `black` to `requirements.txt` and a pre-commit
hook if you want it enforced).
