"""Fetch the universe of NSE symbols to scan.

Sources (in order of preference):
1. nsepython's equity list endpoint (live NSE data).
2. A bundled static CSV fallback (data/nse_equity_list.csv) so the scanner
   still works if NSE's endpoints are rate-limiting or unreachable.

All symbols are returned in Yahoo Finance format (e.g. "RELIANCE.NS") so they
work directly with services/data_fetcher.py.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import logger

FALLBACK_CSV = Path(__file__).resolve().parent.parent / "data" / "nse_equity_list.csv"

NIFTY50 = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC",
    "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE", "ASIANPAINT",
    "MARUTI", "TITAN", "SUNPHARMA", "ULTRACEMCO", "NESTLEIND", "WIPRO", "ONGC",
    "NTPC", "POWERGRID", "M&M", "TATAMOTORS", "TATASTEEL", "ADANIENT", "ADANIPORTS",
    "COALINDIA", "BAJAJFINSV", "HCLTECH", "TECHM", "GRASIM", "JSWSTEEL", "DRREDDY",
    "CIPLA", "EICHERMOT", "BRITANNIA", "DIVISLAB", "HEROMOTOCO", "BPCL", "APOLLOHOSP",
    "HINDALCO", "INDUSINDBK", "SBILIFE", "HDFCLIFE", "BAJAJ-AUTO", "TATACONSUM",
    "UPL", "LTIM", "SHREECEM",
]


def get_symbol_universe(universe: str = "ALL_NSE") -> list[str]:
    """Return a list of NSE symbols (without exchange suffix) to scan.

    universe: "ALL_NSE" | "NIFTY50" | "NIFTY500" | "WATCHLIST"
    """
    universe = universe.upper()

    if universe == "NIFTY50":
        return NIFTY50

    if universe == "WATCHLIST":
        from database.db import get_session
        from database.models.watchlist import WatchlistItem
        with get_session() as db:
            items = db.query(WatchlistItem).all()
            return [i.symbol.replace(".NS", "") for i in items]

    if universe in ("ALL_NSE", "NIFTY500"):
        try:
            return _fetch_live_nse_list(top_n=500 if universe == "NIFTY500" else None)
        except Exception as e:
            logger.warning(f"Live NSE symbol fetch failed ({e}); using fallback CSV.")
            return _fallback_list()

    raise ValueError(f"Unknown universe: {universe}")


def _fetch_live_nse_list(top_n: int | None = None) -> list[str]:
    """Pull the full equity list from NSE via nsepython, since it maintains
    an official, regularly-updated master list of listed securities."""
    from nsepython import nse_eq_symbols  # imported lazily; hits NSE website

    symbols = nse_eq_symbols()
    symbols = sorted(set(symbols))
    if top_n:
        symbols = symbols[:top_n]
    logger.info(f"Fetched {len(symbols)} symbols live from NSE.")
    return symbols


def _fallback_list() -> list[str]:
    if FALLBACK_CSV.exists():
        df = pd.read_csv(FALLBACK_CSV)
        return df["symbol"].dropna().unique().tolist()
    logger.warning("No fallback CSV found either; defaulting to NIFTY50.")
    return NIFTY50


def to_yahoo_symbol(nse_symbol: str) -> str:
    """Convert a bare NSE symbol like 'RELIANCE' to Yahoo Finance format."""
    nse_symbol = nse_symbol.strip().upper()
    return nse_symbol if nse_symbol.endswith(".NS") else f"{nse_symbol}.NS"
