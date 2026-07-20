"""Rule-based single/multi-candle pattern detection.

Each function looks at the last 1-3 candles of the OHLC DataFrame and returns
True/False. `detect_all` runs every detector and returns the ones that fired
on the most recent candle, ready to persist to the `patterns` table.
"""
from __future__ import annotations

import pandas as pd


def _body(row) -> float:
    return abs(row.close - row.open)


def _range(row) -> float:
    return row.high - row.low if row.high != row.low else 1e-9


def _upper_wick(row) -> float:
    return row.high - max(row.close, row.open)


def _lower_wick(row) -> float:
    return min(row.close, row.open) - row.low


def is_hammer(df: pd.DataFrame) -> bool:
    r = df.iloc[-1]
    return (_lower_wick(r) >= 2 * _body(r)) and (_upper_wick(r) <= 0.25 * _body(r)) and (_body(r) / _range(r) < 0.4)


def is_shooting_star(df: pd.DataFrame) -> bool:
    r = df.iloc[-1]
    return (_upper_wick(r) >= 2 * _body(r)) and (_lower_wick(r) <= 0.25 * _body(r)) and (_body(r) / _range(r) < 0.4)


def is_doji(df: pd.DataFrame) -> bool:
    r = df.iloc[-1]
    return _body(r) / _range(r) < 0.1


def is_bullish_engulfing(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return (prev.close < prev.open) and (cur.close > cur.open) and \
           (cur.close >= prev.open) and (cur.open <= prev.close)


def is_bearish_engulfing(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return (prev.close > prev.open) and (cur.close < cur.open) and \
           (cur.open >= prev.close) and (cur.close <= prev.open)


def is_morning_star(df: pd.DataFrame) -> bool:
    if len(df) < 3:
        return False
    d1, d2, d3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    return (d1.close < d1.open) and (_body(d2) / _range(d2) < 0.3) and \
           (d3.close > d3.open) and (d3.close > (d1.open + d1.close) / 2)


def is_evening_star(df: pd.DataFrame) -> bool:
    if len(df) < 3:
        return False
    d1, d2, d3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    return (d1.close > d1.open) and (_body(d2) / _range(d2) < 0.3) and \
           (d3.close < d3.open) and (d3.close < (d1.open + d1.close) / 2)


def is_harami(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return _body(cur) < _body(prev) and max(cur.open, cur.close) < max(prev.open, prev.close) \
        and min(cur.open, cur.close) > min(prev.open, prev.close)


def is_piercing_pattern(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return (prev.close < prev.open) and (cur.close > cur.open) and \
           (cur.open < prev.close) and (cur.close > (prev.open + prev.close) / 2) and (cur.close < prev.open)


def is_dark_cloud_cover(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return (prev.close > prev.open) and (cur.close < cur.open) and \
           (cur.open > prev.close) and (cur.close < (prev.open + prev.close) / 2) and (cur.close > prev.open)


def is_inside_bar(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return cur.high < prev.high and cur.low > prev.low


def is_outside_bar(df: pd.DataFrame) -> bool:
    if len(df) < 2:
        return False
    prev, cur = df.iloc[-2], df.iloc[-1]
    return cur.high > prev.high and cur.low < prev.low


# name -> (detector fn, direction)
CANDLESTICK_PATTERNS = {
    "Hammer": (is_hammer, "bullish"),
    "Shooting Star": (is_shooting_star, "bearish"),
    "Doji": (is_doji, "neutral"),
    "Bullish Engulfing": (is_bullish_engulfing, "bullish"),
    "Bearish Engulfing": (is_bearish_engulfing, "bearish"),
    "Morning Star": (is_morning_star, "bullish"),
    "Evening Star": (is_evening_star, "bearish"),
    "Harami": (is_harami, "neutral"),
    "Piercing Pattern": (is_piercing_pattern, "bullish"),
    "Dark Cloud Cover": (is_dark_cloud_cover, "bearish"),
    "Inside Bar": (is_inside_bar, "neutral"),
    "Outside Bar": (is_outside_bar, "neutral"),
}


def detect_all(df: pd.DataFrame) -> list[dict]:
    """Run every candlestick detector against the latest candle(s).
    Returns a list of {"name", "direction"} dicts for patterns that fired."""
    if df.empty or len(df) < 3:
        return []
    hits = []
    for name, (fn, direction) in CANDLESTICK_PATTERNS.items():
        try:
            if fn(df):
                hits.append({"name": name, "direction": direction})
        except Exception:
            continue
    return hits
