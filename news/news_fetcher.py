"""Fetch recent news headlines for a stock via NewsAPI (free tier)."""
from __future__ import annotations

import datetime as dt

import requests

from utils.config import settings
from utils.logger import logger

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_news(company_name: str, symbol: str, days_back: int = 3, page_size: int = 10) -> list[dict]:
    """Return a list of {"headline", "source", "url", "published_at"} dicts.
    Silently returns [] if no API key is configured or the request fails,
    so the scan pipeline degrades gracefully instead of crashing."""
    if not settings.NEWSAPI_KEY:
        logger.debug("NEWSAPI_KEY not set; skipping news fetch.")
        return []

    since = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()
    params = {
        "q": f'"{company_name}" OR {symbol}',
        "from": since,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": settings.NEWSAPI_KEY,
    }
    try:
        resp = requests.get(NEWSAPI_URL, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])
        return [{
            "headline": a.get("title", ""),
            "source": (a.get("source") or {}).get("name", ""),
            "url": a.get("url", ""),
            "published_at": a.get("publishedAt", ""),
        } for a in articles]
    except Exception as e:
        logger.warning(f"News fetch failed for {symbol}: {e}")
        return []
