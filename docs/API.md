# API Reference

Base URL (local): `http://localhost:8000/api/v1`
Interactive docs (Swagger UI): `http://localhost:8000/docs`

All endpoints return JSON. There is no auth layer by default since this is
built as a personal tool — add an API-key middleware in `backend/main.py`
before exposing it publicly.

## Stocks

| Method | Path | Description |
|---|---|---|
| GET | `/stocks?search=&limit=` | List/search stocks by symbol or name |
| GET | `/stocks/{symbol}` | Stock detail + latest indicators/score |
| GET | `/stocks/{symbol}/history?days=250` | Cached OHLCV for charting |

## Scans

| Method | Path | Description |
|---|---|---|
| GET | `/scans/latest?limit=100&min_score=0` | Latest full ranked scan |
| GET | `/scans/top/{category}?limit=20` | `category` ∈ swing, breakout, momentum, penny, dividend, railway, banking, defence, renewable |
| GET | `/heatmap/{index_name}` | `nifty` \| `banknifty` heatmap data |

## Signals

| Method | Path | Description |
|---|---|---|
| GET | `/signals/latest?signal_type=` | Today's signals, optional filter (BUY/SELL/HOLD/STRONG_BUY) |
| GET | `/signals/{symbol}?limit=30` | Signal history for one stock |
| GET | `/backtest/{strategy_name}` | Stored backtest metrics |

## Watchlist

| Method | Path | Body | Description |
|---|---|---|---|
| GET | `/watchlist` | — | List watchlist |
| POST | `/watchlist` | `{"symbol": "TCS", "notes": ""}` | Add symbol |
| DELETE | `/watchlist/{symbol}` | — | Remove symbol |

## Portfolio

| Method | Path | Body | Description |
|---|---|---|---|
| GET | `/portfolio` | — | Holdings + total PnL |
| POST | `/portfolio` | `{"symbol","quantity","buy_price","buy_date"}` | Add a holding |
| DELETE | `/portfolio/{holding_id}` | — | Remove a holding |

## AI Chat

| Method | Path | Body | Description |
|---|---|---|---|
| POST | `/chat` | `{"question": "Should I buy TCS?"}` | Grounded Q&A over latest scan data |

## Reports

| Method | Path | Description |
|---|---|---|
| GET | `/reports/daily.pdf` | Daily top-25 PDF report |
| GET | `/reports/weekly.xlsx` | Last 7 days of signals as Excel |

## Example: curl

```bash
curl http://localhost:8000/api/v1/scans/top/swing?limit=10
curl -X POST http://localhost:8000/api/v1/watchlist \
     -H "Content-Type: application/json" \
     -d '{"symbol": "TCS", "notes": "watching for pullback"}'
```
