"""The swing-trading strategy definition: ties indicators + patterns +
ML + news + scoring + signals + risk into one per-stock evaluation used by
both the live scanner and the backtester."""
from __future__ import annotations

import pandas as pd

from machine_learning.predict import predict_probabilities
from news.news_fetcher import fetch_news
from news.sentiment import aggregate_sentiment
from scanner.candlestick_patterns import detect_all as detect_candlesticks
from scanner.chart_patterns import detect_chart_patterns
from scanner.indicators import compute_all_indicators, latest_snapshot
from scanner.scoring import composite_score
from signals.risk_management import build_risk_plan
from signals.signal_engine import generate_signal


def evaluate_stock(symbol: str, name: str, price_df: pd.DataFrame,
                    fetch_news_flag: bool = True, account_capital: float = 100_000.0) -> dict | None:
    """Run the full pipeline for one stock and return everything needed to
    persist to the DB and render on the dashboard. Returns None if there's
    not enough price history to evaluate confidently."""
    if price_df.empty or len(price_df) < 60:
        return None

    ind_df = compute_all_indicators(price_df)
    snapshot = latest_snapshot(ind_df)
    if not snapshot:
        return None

    candlesticks = detect_candlesticks(ind_df.tail(5))
    chart_patterns = detect_chart_patterns(ind_df)
    all_patterns = candlesticks + chart_patterns

    sentiment = None
    if fetch_news_flag:
        articles = fetch_news(name or symbol, symbol)
        sentiment = aggregate_sentiment([a["headline"] for a in articles])

    ml_predictions = predict_probabilities(ind_df)

    plan = build_risk_plan(snapshot.get("close", 0.0), snapshot.get("atr_14"),
                            account_capital=account_capital)
    scores = composite_score(snapshot, sentiment=sentiment)
    signal = generate_signal(snapshot, all_patterns, sentiment, scores["overall_score"],
                              risk_reward=plan.risk_reward_ratio)

    return {
        "symbol": symbol,
        "snapshot": snapshot,
        "patterns": all_patterns,
        "sentiment": sentiment,
        "ml_predictions": ml_predictions,
        "scores": scores,
        "risk_plan": plan,
        "signal": signal,
    }
