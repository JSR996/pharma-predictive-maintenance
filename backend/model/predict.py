"""
Inference helpers. Loaded once at FastAPI startup.
"""

import os
import numpy as np
import joblib
from functools import lru_cache

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")


@lru_cache(maxsize=1)
def load_bundle() -> dict:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "model.pkl not found. Run: python backend/model/train.py"
        )
    return joblib.load(MODEL_PATH)


def predict_rul(sensor_dict: dict) -> dict:
    """
    sensor_dict: flat dict of feature_name → float value.
    Returns: { rul, anomaly_score, is_anomaly, confidence, status }
    """
    bundle = load_bundle()
    rf = bundle["rf_model"]
    iso = bundle["iso_model"]
    scaler = bundle["scaler"]
    feature_cols = bundle["feature_cols"]
    rul_cap = bundle["rul_cap"]

    # Build feature vector — fill missing with 0
    vec = np.array([[sensor_dict.get(col, 0.0) for col in feature_cols]])
    vec_s = scaler.transform(vec)

    rul = float(rf.predict(vec_s)[0])
    rul = max(0.0, min(rul, float(rul_cap)))

    # IsolationForest: predict() gives -1 = anomaly, 1 = normal.
    # decision_function() is > 0 for normal points and < 0 for anomalies, with the
    # boundary at 0. Map it through a sigmoid centered on that boundary so normal
    # points score well below 0.5 and anomalies above it (1 = most anomalous).
    iso_label = iso.predict(vec_s)[0]
    decision = float(iso.decision_function(vec_s)[0])
    anomaly_score = float(1.0 / (1.0 + np.exp(decision * 20.0)))
    is_anomaly = bool(iso_label == -1)

    # Derive status
    if is_anomaly or rul < 20:
        status = "critical"
    elif rul < 50:
        status = "warning"
    else:
        status = "normal"

    # Confidence: tree agreement (std of predictions)
    tree_preds = np.array([t.predict(vec_s)[0] for t in rf.estimators_])
    confidence = float(1 - np.std(tree_preds) / (rul_cap + 1e-9))
    confidence = round(max(0.0, min(confidence, 1.0)), 4)

    return {
        "rul": round(rul, 1),
        "anomaly_score": round(anomaly_score, 4),
        "is_anomaly": is_anomaly,
        "confidence": confidence,
        "status": status,
    }


def get_feature_importances() -> dict:
    bundle = load_bundle()
    imps = bundle["feature_importances"]
    top = sorted(imps.items(), key=lambda x: x[1], reverse=True)[:10]
    return {k: round(v, 4) for k, v in top}


def get_model_metrics() -> dict:
    bundle = load_bundle()
    return bundle["metrics"]
