"""Feature engineering for the move-probability model.

Features are pure technical-indicator snapshots (no lookahead) so the same
function can build a training set from historical data and a live feature
row from today's indicators.
"""
from __future__ import annotations

import pandas as pd

FEATURE_COLUMNS = [
    "rsi_14", "macd", "macd_hist", "adx_14", "cci_20", "mfi_14",
    "stochrsi_k", "volume_ratio", "atr_14",
    "close_to_ema20", "close_to_ema50", "close_to_ema200",
    "ema20_to_ema50", "bb_position",
]


def build_features(df_ind: pd.DataFrame) -> pd.DataFrame:
    """Given a DataFrame with raw indicator columns (see scanner/indicators.py),
    derive normalized, scale-free features suitable for ML."""
    f = pd.DataFrame(index=df_ind.index)
    close = df_ind["close"]

    f["rsi_14"] = df_ind["rsi_14"]
    f["macd"] = df_ind["macd"]
    f["macd_hist"] = df_ind["macd_hist"]
    f["adx_14"] = df_ind["adx_14"]
    f["cci_20"] = df_ind["cci_20"]
    f["mfi_14"] = df_ind["mfi_14"]
    f["stochrsi_k"] = df_ind["stochrsi_k"]
    f["volume_ratio"] = df_ind["volume_ratio"]
    f["atr_14"] = df_ind["atr_14"] / close  # normalize by price

    f["close_to_ema20"] = (close - df_ind["ema_20"]) / close
    f["close_to_ema50"] = (close - df_ind["ema_50"]) / close
    f["close_to_ema200"] = (close - df_ind["ema_200"]) / close
    f["ema20_to_ema50"] = (df_ind["ema_20"] - df_ind["ema_50"]) / close

    bb_range = (df_ind["bb_upper"] - df_ind["bb_lower"]).replace(0, pd.NA)
    f["bb_position"] = (close - df_ind["bb_lower"]) / bb_range

    return f[FEATURE_COLUMNS]


def build_labels(price_df: pd.DataFrame, horizon_days: int, threshold_pct: float) -> pd.Series:
    """Label = 1 if close moves up by >= threshold_pct within horizon_days,
    else 0. Uses forward-looking max close over the horizon (typical for
    swing-trade "did it hit target" framing) — only ever used for TRAINING,
    never at inference time, so there's no lookahead leakage in production."""
    close = price_df["close"]
    fwd_max = close.shift(-1).rolling(horizon_days, min_periods=1).max().shift(-(horizon_days - 1))
    return (fwd_max >= close * (1 + threshold_pct / 100)).astype(int)
