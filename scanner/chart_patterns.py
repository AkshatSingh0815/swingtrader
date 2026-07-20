"""Rule-based chart/breakout pattern detection over a rolling window.

Approach: find local swing highs/lows (fractals), fit simple trendlines
through them via linear regression, and classify the shape. This is the
pragmatic, explainable way to do this without a labeled chart-image
dataset — no computer vision model required.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _swing_points(df: pd.DataFrame, order: int = 3) -> tuple[list[int], list[int]]:
    """Return indices of local swing highs and swing lows using a simple
    fractal rule: point is higher/lower than `order` neighbours each side."""
    highs, lows = [], []
    h, l = df["high"].values, df["low"].values
    for i in range(order, len(df) - order):
        if h[i] == max(h[i - order:i + order + 1]):
            highs.append(i)
        if l[i] == min(l[i - order:i + order + 1]):
            lows.append(i)
    return highs, lows


def _slope(xs: list[int], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    return float(np.polyfit(xs, ys, 1)[0])


def detect_chart_patterns(df: pd.DataFrame, window: int = 60) -> list[dict]:
    """Analyze the last `window` bars for classic chart patterns.
    Returns a list of {"name", "direction", "confidence"} dicts."""
    if len(df) < window:
        return []
    w = df.tail(window).reset_index(drop=True)
    highs_idx, lows_idx = _swing_points(w, order=3)
    if len(highs_idx) < 2 or len(lows_idx) < 2:
        return []

    high_vals = [w["high"].iloc[i] for i in highs_idx]
    low_vals = [w["low"].iloc[i] for i in lows_idx]
    high_slope = _slope(highs_idx, high_vals)
    low_slope = _slope(lows_idx, low_vals)

    results: list[dict] = []
    close = w["close"].iloc[-1]
    avg_range = (w["high"] - w["low"]).mean()

    # --- Triangles ---
    if abs(high_slope) < 0.05 * avg_range and low_slope > 0.05 * avg_range:
        results.append({"name": "Ascending Triangle", "direction": "bullish", "confidence": 0.6})
    elif high_slope < -0.05 * avg_range and abs(low_slope) < 0.05 * avg_range:
        results.append({"name": "Descending Triangle", "direction": "bearish", "confidence": 0.6})
    elif high_slope < -0.02 * avg_range and low_slope > 0.02 * avg_range:
        results.append({"name": "Symmetrical Triangle", "direction": "neutral", "confidence": 0.5})

    # --- Double Top / Double Bottom ---
    if len(high_vals) >= 2:
        last_two_highs = high_vals[-2:]
        if abs(last_two_highs[0] - last_two_highs[1]) / avg_range < 0.5 and close < min(last_two_highs):
            results.append({"name": "Double Top", "direction": "bearish", "confidence": 0.55})
    if len(low_vals) >= 2:
        last_two_lows = low_vals[-2:]
        if abs(last_two_lows[0] - last_two_lows[1]) / avg_range < 0.5 and close > max(last_two_lows):
            results.append({"name": "Double Bottom", "direction": "bullish", "confidence": 0.55})

    # --- Head and Shoulders / Inverse H&S (needs 3 peaks / troughs) ---
    if len(high_vals) >= 3:
        l_sh, head, r_sh = high_vals[-3:]
        if head > l_sh and head > r_sh and abs(l_sh - r_sh) / avg_range < 0.7:
            results.append({"name": "Head and Shoulders", "direction": "bearish", "confidence": 0.55})
    if len(low_vals) >= 3:
        l_sh, head, r_sh = low_vals[-3:]
        if head < l_sh and head < r_sh and abs(l_sh - r_sh) / avg_range < 0.7:
            results.append({"name": "Inverse Head and Shoulders", "direction": "bullish", "confidence": 0.55})

    # --- Flag / Pennant: strong prior move + tight recent consolidation ---
    prior_move = w["close"].iloc[-window//2] - w["close"].iloc[0]
    recent_range = (w["high"].tail(window // 4) - w["low"].tail(window // 4)).mean()
    if abs(prior_move) > 2 * avg_range and recent_range < 0.6 * avg_range:
        direction = "bullish" if prior_move > 0 else "bearish"
        results.append({"name": "Flag" if abs(high_slope) < abs(low_slope) else "Pennant",
                         "direction": direction, "confidence": 0.5})

    # --- Cup and Handle: U-shaped recovery then small pullback near highs ---
    mid = window // 2
    left, trough, right = w["close"].iloc[0], w["close"].iloc[mid], w["close"].iloc[-1]
    if trough < left * 0.93 and right > left * 0.97 and w["close"].iloc[-5:].std() < 0.03 * left:
        results.append({"name": "Cup and Handle", "direction": "bullish", "confidence": 0.5})

    # --- Breakout / Breakdown vs. recent range ---
    recent_high = w["high"].iloc[:-1].max()
    recent_low = w["low"].iloc[:-1].min()
    if close > recent_high:
        results.append({"name": "Breakout", "direction": "bullish", "confidence": 0.65})
    elif close < recent_low:
        results.append({"name": "Breakdown", "direction": "bearish", "confidence": 0.65})

    return results
