"""Headline sentiment scoring using VADER (lightweight, no GPU/API needed,
good enough for financial headline polarity as a scoring input)."""
from __future__ import annotations

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# Small finance-specific lexicon boost — VADER is tuned for social media,
# so we nudge it with domain terms that matter for stock headlines.
_FINANCE_LEXICON = {
    "upgrade": 2.0, "downgrade": -2.0, "beats estimates": 2.5, "misses estimates": -2.5,
    "record profit": 2.5, "loss": -1.5, "fraud": -3.0, "scam": -3.0, "buyback": 1.5,
    "rating cut": -2.0, "rating upgrade": 2.0, "default": -3.0, "expansion": 1.2,
    "order win": 2.0, "contract win": 2.0, "regulatory action": -2.0, "penalty": -2.0,
}
_analyzer.lexicon.update(_FINANCE_LEXICON)


def score_headline(headline: str) -> dict:
    """Return {"label": positive|neutral|negative, "score": -1..1}."""
    if not headline:
        return {"label": "neutral", "score": 0.0}
    compound = _analyzer.polarity_scores(headline)["compound"]
    if compound >= 0.2:
        label = "positive"
    elif compound <= -0.2:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "score": compound}


def aggregate_sentiment(headlines: list[str]) -> dict:
    """Average sentiment across a batch of headlines for one stock/day.
    Returns {"label", "score", "positive_count", "negative_count", "neutral_count"}."""
    if not headlines:
        return {"label": "neutral", "score": 0.0, "positive_count": 0,
                 "negative_count": 0, "neutral_count": 0}
    scored = [score_headline(h) for h in headlines]
    avg = sum(s["score"] for s in scored) / len(scored)
    counts = {"positive_count": 0, "negative_count": 0, "neutral_count": 0}
    for s in scored:
        counts[f"{s['label']}_count"] += 1
    label = "positive" if avg >= 0.2 else "negative" if avg <= -0.2 else "neutral"
    return {"label": label, "score": avg, **counts}
