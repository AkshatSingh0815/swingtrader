"""Tests for signals/signal_engine.py and signals/risk_management.py."""
from signals.risk_management import build_risk_plan
from signals.signal_engine import evaluate_buy_conditions, evaluate_sell_conditions, generate_signal


def test_build_risk_plan_basic():
    plan = build_risk_plan(close=100, atr=2, account_capital=100_000, risk_per_trade_pct=1)
    assert plan.entry == 100
    assert plan.stop_loss < plan.entry
    assert plan.target_1 > plan.entry
    assert plan.target_2 > plan.target_1
    assert plan.target_3 > plan.target_2
    assert plan.position_size > 0
    assert plan.risk_reward_ratio > 0


def test_build_risk_plan_missing_atr_uses_fallback():
    plan = build_risk_plan(close=200, atr=None)
    assert plan.stop_loss < 200


def test_evaluate_buy_conditions_strong_setup():
    ind = {"close": 110, "ema_20": 105, "ema_50": 100, "rsi_14": 60,
           "macd": 2, "macd_signal": 1, "adx_14": 30, "volume_ratio": 2.5}
    patterns = [{"name": "Bullish Engulfing", "direction": "bullish"}]
    sentiment = {"label": "positive", "score": 0.5}
    is_buy, reasons = evaluate_buy_conditions(ind, patterns, sentiment, risk_reward=2.5)
    assert is_buy
    assert len(reasons) >= 6


def test_evaluate_sell_conditions_bearish_setup():
    ind = {"macd": -1, "macd_signal": 0, "ema_20": 95, "ema_50": 100, "supertrend_dir": -1}
    patterns = [{"name": "Evening Star", "direction": "bearish"}]
    is_sell, reasons = evaluate_sell_conditions(ind, patterns, {"label": "negative", "score": -0.4})
    assert is_sell
    assert len(reasons) >= 2


def test_generate_signal_returns_valid_type():
    ind = {"close": 110, "ema_20": 105, "ema_50": 100, "rsi_14": 60,
           "macd": 2, "macd_signal": 1, "adx_14": 30, "volume_ratio": 2.5}
    result = generate_signal(ind, [], None, overall_score=85)
    assert result["signal_type"] in ("BUY", "STRONG_BUY", "SELL", "HOLD")
