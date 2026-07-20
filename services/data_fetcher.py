"""Fetches OHLCV price history for NSE stocks, with local DB caching so we
never re-download data we already have, and graceful retry/backoff so one
flaky ticker doesn't kill a 2000-stock scan.
"""
from __future__ import annotations

import datetime as dt
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

from database.db import get_session
from database.models.stock import PriceHistory, Stock
from services.nse_symbols import to_yahoo_symbol
from utils.config import settings
from utils.logger import logger


def fetch_history(symbol: str, period: str = "2y", retries: int = 3) -> pd.DataFrame:
    """Fetch OHLCV for one symbol from Yahoo Finance. Returns empty df on failure."""
    ysym = to_yahoo_symbol(symbol)
    for attempt in range(1, retries + 1):
        try:
            df = yf.Ticker(ysym).history(period=period, interval="1d", auto_adjust=True)
            if df.empty:
                raise ValueError("empty response")
            df = df.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]]
            df.index = df.index.date
            df.index.name = "date"
            return df
        except Exception as e:
            wait = 1.5 * attempt
            logger.debug(f"[{symbol}] fetch attempt {attempt} failed: {e}. Retrying in {wait}s")
            time.sleep(wait)
    logger.warning(f"[{symbol}] failed to fetch history after {retries} attempts.")
    return pd.DataFrame()


def cache_to_db(symbol: str, df: pd.DataFrame) -> None:
    """Upsert fetched OHLCV rows into price_history, and ensure a Stock row exists."""
    if df.empty:
        return
    with get_session() as db:
        if not db.query(Stock).filter_by(symbol=symbol).first():
            db.add(Stock(symbol=symbol, name=symbol))
            db.flush()

        existing_dates = {
            d for (d,) in db.query(PriceHistory.date).filter(PriceHistory.symbol == symbol)
        }
        new_rows = [
            PriceHistory(
                symbol=symbol, date=idx, open=row.open, high=row.high,
                low=row.low, close=row.close, volume=int(row.volume),
            )
            for idx, row in df.iterrows() if idx not in existing_dates
        ]
        db.add_all(new_rows)


def fetch_universe(symbols: list[str], period: str = "2y",
                    max_workers: int | None = None) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV for many symbols in parallel, filtering out illiquid /
    too-cheap stocks per MIN_PRICE / MIN_AVG_VOLUME so the scan focuses on
    tradeable names."""
    max_workers = max_workers or settings.MAX_WORKERS
    results: dict[str, pd.DataFrame] = {}

    def _job(sym: str) -> tuple[str, pd.DataFrame]:
        return sym, fetch_history(sym, period=period)

    logger.info(f"Fetching {len(symbols)} symbols with {max_workers} workers...")
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_job, s): s for s in symbols}
        for i, fut in enumerate(as_completed(futures), 1):
            sym, df = fut.result()
            if df.empty:
                continue
            last_close = df["close"].iloc[-1]
            avg_vol = df["volume"].tail(20).mean()
            if last_close < settings.MIN_PRICE or avg_vol < settings.MIN_AVG_VOLUME:
                continue
            results[sym] = df
            cache_to_db(sym, df)
            if i % 100 == 0:
                logger.info(f"  ...fetched {i}/{len(symbols)}")

    logger.info(f"Fetch complete: {len(results)}/{len(symbols)} symbols passed liquidity filters.")
    return results


def get_cached_history(symbol: str, lookback_days: int = 500) -> pd.DataFrame:
    """Read cached OHLCV straight from the DB (fast path for API/dashboard reads)."""
    with get_session() as db:
        cutoff = dt.date.today() - dt.timedelta(days=lookback_days * 1.6)  # trading days buffer
        rows = (
            db.query(PriceHistory)
            .filter(PriceHistory.symbol == symbol, PriceHistory.date >= cutoff)
            .order_by(PriceHistory.date)
            .all()
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([{
        "date": r.date, "open": r.open, "high": r.high,
        "low": r.low, "close": r.close, "volume": r.volume,
    } for r in rows]).set_index("date")
    return df
