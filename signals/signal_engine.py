"""Turns indicators + patterns + score into a concrete BUY / STRONG_BUY /
SELL / HOLD signal with a human-readable list of reasons, per the rules the
user specified (EMA stack, RSI band, MACD, ADX, volume surge, pattern
confirmation, news, risk:reward)."""
from __future__ import annotations


def evaluate_buy_conditions(ind: dict, patterns: list[dict], sentiment: dict | None,
                             risk_reward: float | None) -> tuple[bool, list[str]]:
    reasons = []
    conditions_met = 0
    total_conditions = 9

    close, ema20, ema50 = ind.get("close"), ind.get("ema_20"), ind.get("ema_50")
    if close and ema20 and close > ema20:
        conditions_met += 1
        reasons.append("Price above EMA20")
    if ema20 and ema50 and ema20 > ema50:
        conditions_met += 1
        reasons.append("EMA20 above EMA50 (uptrend)")

    rsi = ind.get("rsi_14")
    if rsi is not None and 55 <= rsi <= 70:
        conditions_met += 1
        reasons.append(f"RSI in bullish zone ({rsi:.1f})")

    if ind.get("macd") is not None and ind.get("macd_signal") is not None and ind["macd"] > ind["macd_signal"]:
        conditions_met += 1
        reasons.append("MACD bullish crossover")

    adx = ind.get("adx_14")
    if adx is not None and adx > 25:
        conditions_met += 1
        reasons.append(f"Strong trend (ADX {adx:.1f})")

    vol_ratio = ind.get("volume_ratio")
    if vol_ratio is not None and vol_ratio > 2.0:
        conditions_met += 1
        reasons.append(f"Volume surge ({vol_ratio:.1f}x average)")

    if sentiment and sentiment.get("label") == "positive":
        conditions_met += 1
        reasons.append("Positive news sentiment")

    bullish_patterns = [p["name"] for p in patterns if p.get("direction") == "bullish"]
    if bullish_patterns:
        conditions_met += 1
        reasons.append(f"Bullish pattern: {', '.join(bullish_patterns)}")

    if risk_reward is not None and risk_reward >= 2.0:
        conditions_met += 1
        reasons.append(f"Favorable risk:reward ({risk_reward:.1f}:1)")

    is_buy = conditions_met >= 6  # majority of conditions must align
    return is_buy, reasons


def evaluate_sell_conditions(ind: dict, patterns: list[dict], sentiment: dict | None) -> tuple[bool, list[str]]:
    reasons = []
    triggered = 0

    if ind.get("macd") is not None and ind.get("macd_signal") is not None and ind["macd"] < ind["macd_signal"]:
        triggered += 1
        reasons.append("MACD bearish crossover")

    ema20, ema50 = ind.get("ema_20"), ind.get("ema_50")
    if ema20 and ema50 and ema20 < ema50:
        triggered += 1
        reasons.append("EMA20 crossed below EMA50")

    if ind.get("supertrend_dir") == -1:
        triggered += 1
        reasons.append("SuperTrend flipped bearish")

    bearish_patterns = [p["name"] for p in patterns if p.get("direction") == "bearish"]
    if bearish_patterns:
        triggered += 1
        reasons.append(f"Bearish pattern: {', '.join(bearish_patterns)}")

    if sentiment and sentiment.get("label") == "negative":
        triggered += 1
        reasons.append("Negative news sentiment")

    is_sell = triggered >= 2
    return is_sell, reasons


def classify_signal(overall_score: float, is_buy: bool, is_sell: bool) -> str:
    if is_sell:
        return "SELL"
    if is_buy and overall_score >= 80:
        return "STRONG_BUY"
    if is_buy:
        return "BUY"
    return "HOLD"


def generate_signal(ind: dict, patterns: list[dict], sentiment: dict | None,
                     overall_score: float, risk_reward: float | None = None) -> dict:
    is_buy, buy_reasons = evaluate_buy_conditions(ind, patterns, sentiment, risk_reward)
    is_sell, sell_reasons = evaluate_sell_conditions(ind, patterns, sentiment)
    signal_type = classify_signal(overall_score, is_buy, is_sell)
    return {
        "signal_type": signal_type,
        "reasons": {"buy_reasons": buy_reasons, "sell_reasons": sell_reasons},
    }
