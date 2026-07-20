"""Buckets each scan result into the dashboard categories the user asked
for: Top Swing Trades, Breakouts, Momentum, Penny Stocks, Dividend Stocks,
and the sector buckets (Railway/Banking/Defence/Renewable)."""
from __future__ import annotations

SECTOR_KEYWORDS = {
    "railway": ["railway"],
    "banking": ["bank", "banking", "financial services"],
    "defence": ["defence", "defense"],
    "renewable": ["renewable", "green", "solar", "power"],
}


def categorize(symbol: str, sector: str, snapshot: dict, patterns: list[dict],
                scores: dict, fundamentals: dict | None = None) -> list[str]:
    """A stock can belong to multiple categories."""
    cats = []
    close = snapshot.get("close", 0)
    sector_l = (sector or "").lower()

    if scores["overall_score"] >= 70:
        cats.append("swing")

    if any(p["name"] in ("Breakout", "Ascending Triangle", "Cup and Handle") for p in patterns):
        cats.append("breakout")

    if snapshot.get("rsi_14", 0) and snapshot["rsi_14"] > 60 and snapshot.get("volume_ratio", 0) > 1.5:
        cats.append("momentum")

    if close and close < 50:
        cats.append("penny")

    dividend_yield = (fundamentals or {}).get("dividend_yield")
    if dividend_yield and dividend_yield > 2.0:
        cats.append("dividend")

    for cat, keywords in SECTOR_KEYWORDS.items():
        if any(kw in sector_l for kw in keywords):
            cats.append(cat)

    return cats or ["uncategorized"]
