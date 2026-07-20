"""Load trained models and produce move-probability predictions at scan time."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from machine_learning.features import build_features
from machine_learning.train_model import HORIZONS, MODEL_DIR, THRESHOLDS
from utils.logger import logger


@lru_cache(maxsize=None)
def _load_model(horizon: int, threshold: int):
    path = MODEL_DIR / f"model_h{horizon}_t{threshold}.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def predict_probabilities(df_ind: pd.DataFrame) -> list[dict]:
    """Return [{"horizon_days", "threshold_pct", "probability"}] for the
    latest row of indicators. Falls back to an empty list if no trained
    model is available yet (e.g. before the first `train_model.py` run) so
    the scan pipeline never breaks on a missing model file."""
    if df_ind.empty:
        return []
    features = build_features(df_ind).iloc[[-1]]
    if features.isna().any(axis=None):
        return []  # not enough history yet for a clean feature row

    results = []
    for horizon in HORIZONS:
        for threshold in THRESHOLDS:
            model = _load_model(horizon, threshold)
            if model is None:
                continue
            try:
                proba = float(model.predict_proba(features)[0, 1])
            except Exception as e:
                logger.debug(f"Prediction failed h={horizon} t={threshold}: {e}")
                continue
            results.append({"horizon_days": horizon, "threshold_pct": threshold, "probability": proba})
    return results
