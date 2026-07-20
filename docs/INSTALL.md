# Installation Guide

## 1. Prerequisites
- Python 3.11 or 3.12
- Git
- (Optional) Docker + Docker Compose
- (Optional) A free NewsAPI.org key for news sentiment
- (Optional) A Telegram bot token (via @BotFather) and/or an SMTP app password for alerts

## 2. Local setup

```bash
git clone <your-repo-url>
cd swingtrader
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- Leave `NEWSAPI_KEY` blank if you don't want news sentiment yet — the
  pipeline degrades gracefully (news_score defaults to neutral 50).
- Set `SCAN_UNIVERSE=NIFTY50` for your first run (fast, ~1 minute) before
  switching to `ALL_NSE` (slower, ~2000 stocks, can take 20-60+ minutes
  depending on your connection and worker count).

## 3. First scan

```bash
python -m scanner.scan_runner
```

This creates `database/swingtrader.db`, fetches price history, computes
indicators, detects patterns, scores every stock, and writes signals.
Check `logs/scan_<date>.log` for details.

## 4. (Optional) Train the ML model

```bash
python -m machine_learning.train_model
```

Trains 12 models (3 horizons × 4 thresholds) on NIFTY50 history by default.
Edit `machine_learning/train_model.py`'s `train_all()` call to pass a wider
symbol list (e.g. NIFTY500) for better generalization — this takes longer
and downloads 5 years of history per symbol.

## 5. Run the API and dashboard

```bash
# Terminal 1
uvicorn backend.main:app --reload

# Terminal 2
streamlit run frontend/app.py
```

- API: http://localhost:8000/docs
- Dashboard: http://localhost:8501

## 6. Automate it — no PC required (GitHub Actions)

1. Push this repo to GitHub.
2. Go to `Settings → Secrets and variables → Actions` and add (all optional
   except none are strictly required):
   - `NEWSAPI_KEY`
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - `SMTP_USER`, `SMTP_PASSWORD`, `ALERT_EMAIL_TO`
3. The workflow in `.github/workflows/daily_scan.yml` runs automatically
   every weekday at 18:30 IST and commits the updated DB back to your repo.
4. Trigger it manually any time from the **Actions** tab → "Daily NSE Swing
   Scan" → "Run workflow".
5. Pull the latest DB (`git pull`) and open the dashboard locally, or deploy
   the dashboard itself (see below) so you don't need to pull manually.

## 7. Docker

```bash
docker compose up -d backend frontend     # long-running services
docker compose run scanner                # one-off manual scan
```

## 8. Deploying to Render / Railway

- **Backend**: deploy as a Web Service, build command `pip install -r
  requirements.txt`, start command `uvicorn backend.main:app --host 0.0.0.0
  --port $PORT`.
- **Frontend**: deploy as a second Web Service, start command `streamlit run
  frontend/app.py --server.address 0.0.0.0 --server.port $PORT`.
- **Scanner**: use Render's/Railway's Cron Job feature instead of (or in
  addition to) GitHub Actions, pointing at `python -m scanner.scan_runner`.
- Mount a persistent disk for `database/` on whichever platform runs the
  scanner, or point `DATABASE_URL` at a managed Postgres instance for true
  multi-service persistence (requires swapping the SQLite connection string
  only — SQLAlchemy handles the rest).
