"""Tests for scanner/indicators.py using synthetic OHLCV data."""
import numpy as np
import pandas as pd
import pytest

from scanner.indicators import compute_all_indicators, latest_snapshot


@pytest.fixture
def sample_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 300
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    close = 100 + np.cumsum(rng.normal(0.1, 1.5, n))
    high = close + rng.uniform(0.5, 2, n)
    low = close - rng.uniform(0.5, 2, n)
    open_ = close + rng.normal(0, 1, n)
    volume = rng.integers(100_000, 1_000_000, n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume},
                         index=dates.date)


def test_compute_all_indicators_adds_columns(sample_df):
    result = compute_all_indicators(sample_df)
    for col in ["rsi_14", "macd", "ema_20", "ema_50", "ema_200", "atr_14", "adx_14", "obv"]:
        assert col in result.columns


def test_compute_all_indicators_short_df_returns_unchanged():
    tiny_df = pd.DataFrame({"open": [1, 2], "high": [1, 2], "low": [1, 2],
                             "close": [1, 2], "volume": [100, 100]})
    result = compute_all_indicators(tiny_df)
    assert "rsi_14" not in result.columns


def test_latest_snapshot_handles_nan(sample_df):
    result = compute_all_indicators(sample_df)
    snap = latest_snapshot(result)
    assert "close" in snap
    assert isinstance(snap["close"], float)


def test_latest_snapshot_empty_df():
    assert latest_snapshot(pd.DataFrame()) == {}
