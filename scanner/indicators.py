"""Computes the full indicator set for a single stock's OHLCV DataFrame.

Input: DataFrame indexed by date with columns open/high/low/close/volume.
Output: the same DataFrame with indicator columns appended, ready to be
written to the `indicators` table (see database/models/indicator.py) or fed
into scanner/scoring.py.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pandas_ta as ta


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Append every indicator required by the scoring/signal engines.
    Expects at least ~250 rows for EMA200/Ichimoku to be meaningful."""
    if df.empty or len(df) < 30:
        return df

    out = df.copy()

    # --- Trend: EMA / SMA ---
    out["ema_20"] = ta.ema(out["close"], length=20)
    out["ema_50"] = ta.ema(out["close"], length=50)
    out["ema_200"] = ta.ema(out["close"], length=200)
    out["sma_20"] = ta.sma(out["close"], length=20)
    out["sma_50"] = ta.sma(out["close"], length=50)

    # --- VWAP (rolling, since this is daily-bar VWAP proxy not intraday) ---
    typical_price = (out["high"] + out["low"] + out["close"]) / 3
    out["vwap"] = (typical_price * out["volume"]).cumsum() / out["volume"].cumsum()

    # --- Momentum: RSI, Stochastic RSI, MACD, CCI, MFI ---
    out["rsi_14"] = ta.rsi(out["close"], length=14)

    macd = ta.macd(out["close"], fast=12, slow=26, signal=9)
    if macd is not None:
        out["macd"] = macd.iloc[:, 0]
        out["macd_hist"] = macd.iloc[:, 1]
        out["macd_signal"] = macd.iloc[:, 2]

    stochrsi = ta.stochrsi(out["close"], length=14, rsi_length=14, k=3, d=3)
    if stochrsi is not None:
        out["stochrsi_k"] = stochrsi.iloc[:, 0]
        out["stochrsi_d"] = stochrsi.iloc[:, 1]

    out["cci_20"] = ta.cci(out["high"], out["low"], out["close"], length=20)
    out["mfi_14"] = ta.mfi(out["high"], out["low"], out["close"], out["volume"], length=14)

    # --- Volatility: ATR, Bollinger Bands ---
    out["atr_14"] = ta.atr(out["high"], out["low"], out["close"], length=14)
    bb = ta.bbands(out["close"], length=20, std=2)
    if bb is not None:
        out["bb_lower"] = bb.iloc[:, 0]
        out["bb_mid"] = bb.iloc[:, 1]
        out["bb_upper"] = bb.iloc[:, 2]

    # --- Trend strength: ADX, SuperTrend ---
    adx = ta.adx(out["high"], out["low"], out["close"], length=14)
    if adx is not None:
        out["adx_14"] = adx.iloc[:, 0]

    st = ta.supertrend(out["high"], out["low"], out["close"], length=10, multiplier=3)
    if st is not None:
        out["supertrend"] = st.iloc[:, 0]
        out["supertrend_dir"] = st.iloc[:, 1]

    # --- Volume ---
    out["volume_avg_20"] = out["volume"].rolling(20).mean()
    out["volume_ratio"] = out["volume"] / out["volume_avg_20"]
    out["obv"] = ta.obv(out["close"], out["volume"])

    # --- Ichimoku Cloud ---
    ichimoku = ta.ichimoku(out["high"], out["low"], out["close"])
    if ichimoku is not None and isinstance(ichimoku, tuple):
        span_df, _ = ichimoku
        out["ichimoku_conv"] = span_df.get("ITS_9")
        out["ichimoku_base"] = span_df.get("IKS_26")
        out["ichimoku_span_a"] = span_df.get("ISA_9")
        out["ichimoku_span_b"] = span_df.get("ISB_26")

    return out


def latest_snapshot(df_with_indicators: pd.DataFrame) -> dict:
    """Return the most recent row as a flat dict, safe against NaNs (-> None)."""
    if df_with_indicators.empty:
        return {}
    row = df_with_indicators.iloc[-1]
    return {k: (None if pd.isna(v) else float(v) if isinstance(v, (int, float, np.floating)) else v)
            for k, v in row.to_dict().items()}
