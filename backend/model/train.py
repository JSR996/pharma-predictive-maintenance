"""
Train predictive maintenance models on NASA CMAPSS FD001 dataset.
Outputs: backend/model/model.pkl

Usage: python backend/model/train.py
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Feature engineering is shared with the live inference path (simulator.py) so the
# two can never drift — see model/features.py.
from features import (
    WINDOW, DROP_SENSORS, RAW_COLS, OP_COLS,
    add_rolling_features, feature_columns,
)

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

COLS = RAW_COLS

RUL_CAP = 125          # Standard CMAPSS cap — degradation only relevant near failure
ANOMALY_QUANTILE = 0.95  # flag a reading if it's more anomalous than 95% of healthy operation
ANOMALY_REF_SAMPLES = 2000  # downsampled calibration reference kept in the bundle
CONFORMAL_ALPHA = 0.10   # split-conformal miscoverage → 90% RUL prediction intervals


# ─── Data Loading ─────────────────────────────────────────────────────────────
def load_cmapss(split: str = "train") -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{split}_FD001.txt")
    if not os.path.exists(path):
        sys.exit(
            f"\n❌ Data not found at {path}\n"
            "Run: python scripts/download_data.py\n"
        )
    df = pd.read_csv(path, sep=r"\s+", header=None, names=COLS)
    df.drop(columns=DROP_SENSORS, inplace=True)
    return df


def add_rul(df: pd.DataFrame) -> pd.DataFrame:
    max_cycle = df.groupby("unit")["cycle"].max().rename("max_cycle")
    df = df.join(max_cycle, on="unit")
    df["RUL"] = (df["max_cycle"] - df["cycle"]).clip(upper=RUL_CAP)
    df.drop(columns=["max_cycle"], inplace=True)
    return df


# ─── Feature Engineering ──────────────────────────────────────────────────────
def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    sensor_cols = [c for c in df.columns if c.startswith("s")]
    df = add_rolling_features(df, sensor_cols)
    feature_cols = feature_columns(sensor_cols)
    return df, feature_cols


# ─── Training ────────────────────────────────────────────────────────────────
def train():
    print("📦 Loading CMAPSS FD001...")
    train_df = load_cmapss("train")
    train_df = add_rul(train_df)
    train_df, feature_cols = build_features(train_df)

    X = train_df[feature_cols].values
    y = train_df["RUL"].values
    groups = train_df["unit"].values

    # Split by ENGINE UNIT, not by row. Rolling-window features make consecutive
    # cycles of the same unit nearly identical, so a plain random row split leaks
    # the answer across train/val and badly inflates R². GroupShuffleSplit keeps all
    # cycles of any given unit entirely on one side of the split.
    gss = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
    train_idx, val_idx = next(gss.split(X, y, groups))
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]

    # Scale features
    scaler = MinMaxScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)

    # ── RUL Model ────────────────────────────────────────────────────────────
    print("🌲 Training RandomForest (RUL prediction)...")
    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        n_jobs=-1,
        random_state=42,
    )
    rf.fit(X_train_s, y_train)

    y_pred = rf.predict(X_val_s)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    mae = mean_absolute_error(y_val, y_pred)
    r2 = r2_score(y_val, y_pred)
    print(f"   RMSE: {rmse:.2f} | MAE: {mae:.2f} | R²: {r2:.4f}")

    # Split-conformal calibration: the (1-alpha) quantile of absolute residuals on
    # the held-out (group-split) validation set. At inference, rul ± conformal_q is a
    # genuinely calibrated ~90% prediction interval — no hand-tuned constant. This is
    # a real predictive-uncertainty band (unlike `ensemble_agreement`, which only
    # measures tree consensus).
    residuals = np.abs(y_val - y_pred)
    conformal_q = float(np.quantile(residuals, 1.0 - CONFORMAL_ALPHA))
    print(f"   conformal interval: ±{conformal_q:.1f} cycles "
          f"({(1-CONFORMAL_ALPHA)*100:.0f}% target coverage)")

    # ── Anomaly Model ────────────────────────────────────────────────────────
    # Train on the HEALTHY regime only (the capped-RUL plateau = far from failure),
    # so "anomalous" means "departs from healthy operation" rather than "is a rare
    # degradation state" — degradation is already captured by the RUL model.
    print("🔍 Training IsolationForest (anomaly detection, healthy baseline)...")
    healthy_mask = y_train >= RUL_CAP
    X_healthy = X_train_s[healthy_mask]
    iso = IsolationForest(
        n_estimators=100,
        contamination="auto",   # irrelevant: we calibrate + threshold ourselves
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_healthy)

    # Calibration: the empirical distribution of decision_function over healthy
    # operation. At inference, a live score becomes the fraction of healthy data at
    # least as "normal" as it (a real percentile) — no magic sigmoid constant. We
    # keep a downsampled, sorted copy in the bundle.
    healthy_scores = np.sort(iso.decision_function(X_healthy))
    if len(healthy_scores) > ANOMALY_REF_SAMPLES:
        idx = np.linspace(0, len(healthy_scores) - 1, ANOMALY_REF_SAMPLES).astype(int)
        anomaly_ref_scores = healthy_scores[idx]
    else:
        anomaly_ref_scores = healthy_scores
    # Decision value below which a reading is flagged (the 5th percentile of healthy
    # decision scores, since lower decision = more anomalous).
    anomaly_threshold = float(np.quantile(healthy_scores, 1.0 - ANOMALY_QUANTILE))
    print(f"   healthy rows: {len(X_healthy)} | "
          f"flag below decision={anomaly_threshold:.4f} (top {(1-ANOMALY_QUANTILE)*100:.0f}%)")

    # ── Feature importance ───────────────────────────────────────────────────
    importances = dict(zip(feature_cols, rf.feature_importances_.tolist()))
    top10 = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\n🏆 Top 10 features:")
    for feat, imp in top10:
        print(f"   {feat:<25} {imp:.4f}")

    # ── Save ─────────────────────────────────────────────────────────────────
    bundle = {
        "rf_model": rf,
        "iso_model": iso,
        "scaler": scaler,
        "feature_cols": feature_cols,
        "rul_cap": RUL_CAP,
        "metrics": {"rmse": rmse, "mae": mae, "r2": r2},
        "feature_importances": importances,
        "anomaly_ref_scores": anomaly_ref_scores,
        "anomaly_quantile": ANOMALY_QUANTILE,
        "conformal_q": conformal_q,
        "conformal_alpha": CONFORMAL_ALPHA,
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\n✅ Model saved → {MODEL_PATH}")


if __name__ == "__main__":
    train()
