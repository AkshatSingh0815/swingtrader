"""AI assistant endpoint: answers questions like 'Should I buy Tata Motors?'
or 'Explain RSI' by grounding answers in the latest scan data already in the
DB (not by calling an external LLM — keeps this self-contained and free to
run). Swap `answer_question` for an LLM call if you want richer, more
conversational answers; the retrieval/grounding logic stays the same."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.indicator import Indicator
from database.models.score import Score
from database.models.signal import Signal

router = APIRouter()

INDICATOR_EXPLANATIONS = {
    "rsi": "RSI (Relative Strength Index) measures the speed and size of recent price "
           "moves on a 0-100 scale. Above 70 is often considered overbought, below 30 "
           "oversold. This strategy looks for RSI between 55-70 as a healthy bullish zone.",
    "macd": "MACD (Moving Average Convergence Divergence) compares a fast and slow EMA. "
            "When the MACD line crosses above its signal line, it's a bullish trigger; "
            "crossing below is bearish.",
    "adx": "ADX (Average Directional Index) measures trend STRENGTH, not direction. "
           "Above 25 usually means a strong trend (up or down) is in place.",
    "atr": "ATR (Average True Range) measures volatility. This platform uses it to size "
           "stop-losses so they adapt to how much a stock typically moves.",
    "supertrend": "SuperTrend is a trend-following overlay that flips above/below price "
                  "to signal trend direction changes.",
    "bollinger": "Bollinger Bands plot a moving average with bands at +/- N standard "
                 "deviations, showing relative highs/lows and volatility squeezes.",
}


class ChatQuery(BaseModel):
    question: str


@router.post("/chat")
def chat(query: ChatQuery, db: Session = Depends(get_db)):
    q = query.question.lower().strip()

    for key, explanation in INDICATOR_EXPLANATIONS.items():
        if key in q or (key == "adx" and "adx" in q):
            return {"answer": explanation}

    symbol = _extract_symbol(q, db)
    if symbol:
        return {"answer": _explain_stock(symbol, db)}

    return {"answer": "I can explain indicators (RSI, MACD, ADX, ATR, SuperTrend, Bollinger "
                       "Bands) or evaluate a specific NSE stock — try 'Should I buy RELIANCE?' "
                       "or 'Explain RSI'."}


def _extract_symbol(question: str, db: Session) -> str | None:
    words = [w.strip("?.,!").upper() for w in question.split()]
    known_symbols = {s[0] for s in db.query(Score.symbol).distinct()}
    for w in words:
        if w in known_symbols:
            return w
    return None


def _explain_stock(symbol: str, db: Session) -> str:
    score = db.query(Score).filter_by(symbol=symbol).order_by(desc(Score.date)).first()
    signal = db.query(Signal).filter_by(symbol=symbol).order_by(desc(Signal.date)).first()
    ind = db.query(Indicator).filter_by(symbol=symbol).order_by(desc(Indicator.date)).first()

    if not score or not signal:
        return f"No recent scan data for {symbol} yet — it may not have been picked up in the last scan."

    reasons = signal.reasons.get("buy_reasons", []) if signal.signal_type in ("BUY", "STRONG_BUY") \
        else signal.reasons.get("sell_reasons", [])
    reason_text = "; ".join(reasons) if reasons else "no strong directional signal"

    return (
        f"{symbol}: overall score {score.overall_score}/100 (rank #{score.rank}). "
        f"Current signal: {signal.signal_type}. Reasoning: {reason_text}. "
        f"Suggested plan — entry {signal.entry}, stop-loss {signal.stop_loss}, "
        f"target1 {signal.target_1}, risk:reward {signal.risk_reward_ratio}:1. "
        f"This is a data-driven ranking, not a guarantee — always size positions "
        f"according to your own risk tolerance."
    )
