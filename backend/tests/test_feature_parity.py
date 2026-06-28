"""
Guards flaw #1: the training feature path (model.features.add_rolling_features,
used by train.py) and the live serving path (model.features.build_feature_row,
used by simulator.py) must produce identical feature vectors for the same cycle.

If these two ever diverge, the dashboard's predictions stop matching what the
model was evaluated on. This test replays real CMAPSS rows through both paths and
asserts every feature matches, including the partial-window cycles at the start of
each engine run.
"""

import os
from collections import deque

import numpy as np
import pandas as pd
import pytest

from model.features import (
    WINDOW, DROP_SENSORS, RAW_COLS, OP_COLS,
    add_rolling_features, build_feature_row, feature_columns,
)

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "train_FD001.txt",
)

TOL = 1e-9


@pytest.fixture(scope="module")
def cmapss_df():
    if not os.path.exists(DATA_PATH):
        pytest.skip(f"CMAPSS data not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, sep=r"\s+", header=None, names=RAW_COLS)
    df.drop(columns=DROP_SENSORS, inplace=True)
    return df


def test_train_and_serve_features_match(cmapss_df):
    df = cmapss_df
    sensor_cols = [c for c in df.columns if c.startswith("s")]

    # Training path: rolling features over the whole frame, grouped by unit.
    trained = add_rolling_features(df.copy(), sensor_cols)
    feat_cols = feature_columns(sensor_cols)

    # Serving path: replay each unit cycle-by-cycle through a trailing deque,
    # exactly as ModelReplaySimulator does.
    sample_units = sorted(df["unit"].unique())[:3]
    compared = 0
    for unit in sample_units:
        unit_rows = (
            df[df["unit"] == unit].sort_values("cycle").to_dict("records")
        )
        trained_unit = (
            trained[trained["unit"] == unit].sort_values("cycle")
            .reset_index(drop=True)
        )
        window: deque = deque(maxlen=WINDOW)
        for i, row in enumerate(unit_rows):
            window.append(row)
            served = build_feature_row(list(window), sensor_cols, OP_COLS)
            expected = trained_unit.iloc[i]
            for col in feat_cols:
                assert np.isclose(served[col], expected[col], rtol=0, atol=TOL), (
                    f"unit {unit} cycle {i} feature {col}: "
                    f"served={served[col]} train={expected[col]}"
                )
            compared += 1

    assert compared > 0


def test_single_cycle_std_is_zero(cmapss_df):
    """A 1-element window must give std 0 in both paths (pandas NaN→0)."""
    df = cmapss_df
    sensor_cols = [c for c in df.columns if c.startswith("s")]
    first_row = df[df["unit"] == df["unit"].iloc[0]].sort_values("cycle").iloc[0]
    served = build_feature_row([first_row.to_dict()], sensor_cols, OP_COLS)
    for s in sensor_cols:
        assert served[f"{s}_std{WINDOW}"] == 0.0
