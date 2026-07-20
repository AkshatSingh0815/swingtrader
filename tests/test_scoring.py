"""Tests for scanner/scoring.py."""
from scanner.scoring import composite_score, fundamental_score, momentum_score, news_score, technical_score


def test_technical_score_bullish_setup():
    ind = {"close": 110, "ema_20": 105, "ema_50": 100, "ema_200": 95,
           "macd": 2, "macd_signal": 1, "supertrend_dir": 1, "adx_14": 30,
           "ichimoku_span_a": 100, "ichimoku_span_b": 98}
    score = technical_score(ind)
    assert score > 70


def test_technical_score_bearish_setup():
    ind = {"close": 90, "ema_20": 95, "ema_50": 100, "ema_200": 105,
           "macd": -2, "macd_signal": -1, "supertrend_dir": -1, "adx_14": 30,
           "ichimoku_span_a": 100, "ichimoku_span_b": 98}
    score = technical_score(ind)
    assert score < 40


def test_momentum_score_healthy_rsi():
    assert momentum_score({"rsi_14": 60, "stochrsi_k": 60, "cci_20": 120, "mfi_14": 65}) > 60


def test_news_score_bounds():
    assert news_score({"score": 1.0}) == 100
    assert news_score({"score": -1.0}) == 0
    assert news_score(None) == 50


def test_fundamental_score_defaults_neutral():
    assert fundamental_score(None) == 50.0


def test_composite_score_weights_sum_correctly():
    ind = {"close": 110, "ema_20": 105, "ema_50": 100, "rsi_14": 60, "volume_ratio": 2.5}
    result = composite_score(ind)
    assert set(result.keys()) == {
        "technical_score", "momentum_score", "volume_score", "news_score",
        "fundamental_score", "overall_score",
    }
    assert 0 <= result["overall_score"] <= 100
