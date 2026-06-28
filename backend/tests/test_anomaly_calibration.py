"""
Guards flaw #2: the anomaly detector must measure departure from HEALTHY
operation, not act as a fixed-rate flag. We assert the calibration direction —
healthy (high-RUL) readings score low and aren't flagged, near-failure readings
score higher and are flagged — and that the score is a real [0,1] value.

Requires a trained model.pkl and the CMAPSS training data; skipped otherwise.
"""

import os

import pandas as pd
import pytest

from model.features import DROP_SENSORS, RAW_COLS, add_rolling_features
from model import predict as predict_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "train_FD001.txt")
MODEL_PATH = os.path.join(BASE, "model", "model.pkl")


@pytest.fixture(scope="module")
def feature_rows():
    if not os.path.exists(DATA_PATH) or not os.path.exists(MODEL_PATH):
        pytest.skip("requires train_FD001.txt and a trained model.pkl")

    predict_mod.load_bundle.cache_clear()  # ensure we read the current bundle
    feature_cols = predict_mod.load_bundle()["feature_cols"]

    df = pd.read_csv(DATA_PATH, sep=r"\s+", header=None, names=RAW_COLS)
    df.drop(columns=DROP_SENSORS, inplace=True)
    max_cycle = df.groupby("unit")["cycle"].max().rename("mc")
    df = df.join(max_cycle, on="unit")
    df["RUL"] = (df["mc"] - df["cycle"]).clip(upper=125)
    sensor_cols = [c for c in df.columns if c.startswith("s")]
    df = add_rolling_features(df, sensor_cols)

    # Sample so the per-row RF inference loop stays fast, but keep enough rows for
    # meaningful flag rates.
    healthy = (
        df[df["RUL"] >= 125].sample(n=200, random_state=0)[feature_cols]
        .to_dict("records")
    )
    failure = (
        df[df["RUL"] <= 5].sample(n=200, random_state=0)[feature_cols]
        .to_dict("records")
    )
    return healthy, failure


def _scores(rows):
    preds = [predict_mod.predict_rul(r) for r in rows]
    return (
        [p["anomaly_score"] for p in preds],
        [p["is_anomaly"] for p in preds],
    )


def test_scores_are_probabilities(feature_rows):
    healthy, failure = feature_rows
    scores, _ = _scores(healthy[:20] + failure[:20])
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_anomaly_rises_toward_failure(feature_rows):
    healthy, failure = feature_rows
    h_scores, h_flags = _scores(healthy)
    f_scores, f_flags = _scores(failure)

    mean = lambda xs: sum(xs) / len(xs)

    # Calibration direction: healthy reads low (folded at the median), near-failure
    # saturates high.
    assert mean(h_scores) < 0.4
    assert mean(f_scores) > 0.9
    assert mean(f_scores) > mean(h_scores)

    # Healthy flag rate stays near the 5% design point (sampling slack); near-failure
    # is flagged the large majority of the time. Not a fixed-rate flag on everything.
    healthy_flag_rate = mean([1 if x else 0 for x in h_flags])
    failure_flag_rate = mean([1 if x else 0 for x in f_flags])
    assert healthy_flag_rate <= 0.15
    assert failure_flag_rate >= 0.60
