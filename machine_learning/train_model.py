"""Train the move-probability model.

For each (horizon_days, threshold_pct) combination, trains an XGBoost
classifier: P(stock closes >= threshold_pct higher within horizon_days).
Run standalone:  python -m machine_learning.train_model
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from machine_learning.features import build_features, build_labels
from scanner.indicators import compute_all_indicators
from services.data_fetcher import fetch_history
from services.nse_symbols import NIFTY50
from utils.logger import logger

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

HORIZONS = [5, 10, 20]
THRESHOLDS = [5, 10, 15, 20]


def build_training_set(symbols: list[str], horizon: int, threshold: float) -> tuple[pd.DataFrame, pd.Series]:
    X_parts, y_parts = [], []
    for sym in symbols:
        raw = fetch_history(sym, period="5y")
        if raw.empty or len(raw) < 300:
            continue
        ind = compute_all_indicators(raw)
        X = build_features(ind)
        y = build_labels(ind, horizon_days=horizon, threshold_pct=threshold)
        combined = pd.concat([X, y.rename("label")], axis=1).dropna()
        if combined.empty:
            continue
        X_parts.append(combined[X.columns])
        y_parts.append(combined["label"])
    if not X_parts:
        return pd.DataFrame(), pd.Series(dtype=int)
    return pd.concat(X_parts), pd.concat(y_parts)


def train_one(symbols: list[str], horizon: int, threshold: float) -> None:
    logger.info(f"Training model: horizon={horizon}d, threshold={threshold}%")
    X, y = build_training_set(symbols, horizon, threshold)
    if X.empty or y.nunique() < 2:
        logger.warning(f"Skipping horizon={horizon} threshold={threshold}: insufficient/degenerate data.")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict_proba(X_test)[:, 1]
    try:
        auc = roc_auc_score(y_test, preds)
        logger.info(f"  AUC = {auc:.3f} (n_train={len(X_train)}, n_test={len(X_test)})")
    except ValueError:
        logger.info("  AUC could not be computed (single-class test split).")

    path = MODEL_DIR / f"model_h{horizon}_t{int(threshold)}.joblib"
    joblib.dump(model, path)
    logger.info(f"  Saved -> {path}")


def train_all(symbols: list[str] | None = None) -> None:
    symbols = symbols or NIFTY50
    for horizon in HORIZONS:
        for threshold in THRESHOLDS:
            train_one(symbols, horizon, threshold)


if __name__ == "__main__":
    train_all()
