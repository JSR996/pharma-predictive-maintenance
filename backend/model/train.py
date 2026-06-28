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

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

COLS = (
    ["unit", "cycle", "op1", "op2", "op3"]
    + [f"s{i}" for i in range(1, 22)]
)

# Sensors with near-zero variance on FD001 — dropped
DROP_SENSORS = ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]

RUL_CAP = 125          # Standard CMAPSS cap — degradation only relevant near failure
WINDOW = 10            # Rolling window for lag features
CONTAMINATION = 0.05   # ~5% anomaly rate for IsolationForest


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


def add_rolling_features(df: pd.DataFrame, sensor_cols: list) -> pd.DataFrame:
    grp = df.groupby("unit")
    for col in sensor_cols:
        df[f"{col}_mean{WINDOW}"] = grp[col].transform(
            lambda x: x.rolling(WINDOW, min_periods=1).mean()
        )
        df[f"{col}_std{WINDOW}"] = grp[col].transform(
            lambda x: x.rolling(WINDOW, min_periods=1).std().fillna(0)
        )
    return df


# ─── Feature Engineering ──────────────────────────────────────────────────────
def build_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    sensor_cols = [c for c in df.columns if c.startswith("s")]
    op_cols = ["op1", "op2", "op3"]
    df = add_rolling_features(df, sensor_cols)
    feature_cols = op_cols + sensor_cols + [
        c for c in df.columns if "_mean" in c or "_std" in c
    ]
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

    # ── Anomaly Model ────────────────────────────────────────────────────────
    print("🔍 Training IsolationForest (anomaly detection)...")
    iso = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_train_s)

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
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\n✅ Model saved → {MODEL_PATH}")


if __name__ == "__main__":
    train()
