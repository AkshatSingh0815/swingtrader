"""Composite scoring engine: blends technical, momentum, volume, news, and
fundamental signals into one 0-100 overall score, using the weights in
utils/config.py (defaults: 40/25/15/10/10)."""
from __future__ import annotations

from utils.config import settings


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def technical_score(ind: dict) -> float:
    """Trend alignment: price vs EMAs, SuperTrend direction, ADX strength,
    Ichimoku cloud position, MACD line vs signal."""
    score = 50.0
    close = ind.get("close")
    ema20, ema50, ema200 = ind.get("ema_20"), ind.get("ema_50"), ind.get("ema_200")

    if close and ema20 and close > ema20:
        score += 10
    if ema20 and ema50 and ema20 > ema50:
        score += 10
    if ema50 and ema200 and ema50 > ema200:
        score += 5
    if ind.get("macd") is not None and ind.get("macd_signal") is not None:
        score += 10 if ind["macd"] > ind["macd_signal"] else -10
    if ind.get("supertrend_dir") == 1:
        score += 10
    elif ind.get("supertrend_dir") == -1:
        score -= 10
    adx = ind.get("adx_14")
    if adx is not None:
        score += 10 if adx > 25 else (0 if adx > 15 else -5)
    span_a, span_b = ind.get("ichimoku_span_a"), ind.get("ichimoku_span_b")
    if close and span_a and span_b:
        score += 5 if close > max(span_a, span_b) else -5

    return _clip(score)


def momentum_score(ind: dict) -> float:
    """RSI positioning, Stochastic RSI, CCI, rate-of-change proxies."""
    score = 50.0
    rsi = ind.get("rsi_14")
    if rsi is not None:
        if 55 <= rsi <= 70:
            score += 20
        elif 45 <= rsi < 55:
            score += 5
        elif rsi > 70:
            score += 5  # overbought but strong; capped, not penalized hard
        elif rsi < 30:
            score -= 15
    stoch_k = ind.get("stochrsi_k")
    if stoch_k is not None:
        score += 10 if stoch_k > 50 else -5
    cci = ind.get("cci_20")
    if cci is not None:
        score += 10 if cci > 100 else (-10 if cci < -100 else 0)
    mfi = ind.get("mfi_14")
    if mfi is not None:
        score += 5 if mfi > 60 else (-5 if mfi < 30 else 0)
    return _clip(score)


def volume_score(ind: dict) -> float:
    """Volume confirmation: current volume vs 20-day average, OBV trend proxy."""
    score = 50.0
    ratio = ind.get("volume_ratio")
    if ratio is not None:
        if ratio >= 2.0:
            score += 30
        elif ratio >= 1.5:
            score += 20
        elif ratio >= 1.0:
            score += 10
        else:
            score -= 10
    return _clip(score)


def news_score(sentiment: dict | None) -> float:
    """sentiment: {"label", "score"(-1..1), ...} from news/sentiment.py."""
    if not sentiment:
        return 50.0
    return _clip(50.0 + sentiment.get("score", 0.0) * 50.0)


def fundamental_score(fundamentals: dict | None) -> float:
    """fundamentals: optional dict with pe_ratio, roe, debt_to_equity, etc.
    Defaults to neutral 50 when data isn't available (keeps composite score
    well-defined even without a fundamentals data source configured)."""
    if not fundamentals:
        return 50.0
    score = 50.0
    pe = fundamentals.get("pe_ratio")
    if pe is not None:
        score += 10 if 0 < pe < 25 else (-10 if pe > 60 else 0)
    roe = fundamentals.get("roe")
    if roe is not None:
        score += 10 if roe > 15 else 0
    de = fundamentals.get("debt_to_equity")
    if de is not None:
        score += 10 if de < 1 else (-10 if de > 2 else 0)
    return _clip(score)


def composite_score(ind: dict, sentiment: dict | None = None,
                     fundamentals: dict | None = None) -> dict:
    """Return all sub-scores plus the final weighted overall score."""
    t = technical_score(ind)
    m = momentum_score(ind)
    v = volume_score(ind)
    n = news_score(sentiment)
    f = fundamental_score(fundamentals)

    overall = (
        t * settings.WEIGHT_TECHNICAL +
        m * settings.WEIGHT_MOMENTUM +
        v * settings.WEIGHT_VOLUME +
        n * settings.WEIGHT_NEWS +
        f * settings.WEIGHT_FUNDAMENTAL
    )
    return {
        "technical_score": round(t, 2),
        "momentum_score": round(m, 2),
        "volume_score": round(v, 2),
        "news_score": round(n, 2),
        "fundamental_score": round(f, 2),
        "overall_score": round(overall, 2),
    }
