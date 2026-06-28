"""
Inference helpers. Loaded once at FastAPI startup.
"""

import os
import numpy as np
import joblib
from functools import lru_cache

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

# RUL status thresholds — the single definition used by both the ML inference path
# and the synthetic fallback simulator, so a unit's status means the same thing in
# either stream mode.
RUL_CRITICAL = 20
RUL_WARNING = 50


def status_for(rul: float, is_anomaly: bool) -> str:
    """critical / warning / normal from a RUL value and anomaly flag."""
    if is_anomaly or rul < RUL_CRITICAL:
        return "critical"
    if rul < RUL_WARNING:
        return "warning"
    return "normal"


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

    # Anomaly = departure from HEALTHY operation, calibrated against the healthy
    # decision_function distribution stored at train time (higher decision = more
    # normal). `rank` is the fraction of healthy operation at most as normal as this
    # reading, so a healthy median point sits at rank≈0.5 and an anomalous point at
    # rank≈0. No magic constant.
    decision = float(iso.decision_function(vec_s)[0])
    ref = bundle.get("anomaly_ref_scores")
    if ref is not None and len(ref):
        ref = np.asarray(ref)            # healthy decision scores, sorted ascending
        rank = float(np.searchsorted(ref, decision, side="right")) / len(ref)
        quantile = float(bundle.get("anomaly_quantile", 0.95))
        # Flag the lower tail: more anomalous than `quantile` of healthy operation
        # (exactly a (1-quantile) false-positive rate on healthy data by design).
        is_anomaly = bool(rank <= (1.0 - quantile))
        # Display score folded at the healthy median: 0 across the normal half of
        # healthy operation, rising to 1 at/below the most anomalous healthy reading.
        anomaly_score = float(min(1.0, max(0.0, 1.0 - 2.0 * rank)))
    else:
        # Backward-compat fallback for an old bundle without calibration data.
        anomaly_score = float(1.0 / (1.0 + np.exp(decision * 20.0)))
        is_anomaly = bool(iso.predict(vec_s)[0] == -1)

    status = status_for(rul, is_anomaly)

    # Ensemble agreement: how tightly the individual trees agree (1 = identical
    # predictions, 0 = spread of a full RUL cap). This measures model *consensus*,
    # NOT calibrated predictive uncertainty — do not read it as a probability.
    tree_preds = np.array([t.predict(vec_s)[0] for t in rf.estimators_])
    ensemble_agreement = float(1 - np.std(tree_preds) / (rul_cap + 1e-9))
    ensemble_agreement = round(max(0.0, min(ensemble_agreement, 1.0)), 4)

    return {
        "rul": round(rul, 1),
        "anomaly_score": round(anomaly_score, 4),
        "is_anomaly": is_anomaly,
        "ensemble_agreement": ensemble_agreement,
        "confidence": ensemble_agreement,  # deprecated alias; prefer ensemble_agreement
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
