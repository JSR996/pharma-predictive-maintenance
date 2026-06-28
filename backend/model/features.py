"""
Shared feature engineering for PharmaGuard.

This is the SINGLE source of truth for the rolling-window features the model is
trained on and served with. Both the offline training path
(`add_rolling_features`, used by model/train.py) and the live inference path
(`build_feature_row`, used by simulator.py) go through this module, so the two
can never drift apart. A parity test (tests/test_feature_parity.py) asserts they
produce identical values cycle-by-cycle.

Windowing contract (must match between both functions):
- For cycle i, the window is the trailing `WINDOW` cycles *including* cycle i.
- Partial windows are allowed at the start of a run (pandas `min_periods=1`).
- Rolling std uses ddof=1; std of a single-element window is 0 (pandas yields
  NaN there, which training fills with 0).
"""

import numpy as np
import pandas as pd

# Rolling window length. Single definition — train.py and simulator.py import it.
WINDOW = 10

# Sensors with near-zero variance on FD001 — dropped everywhere.
DROP_SENSORS = ["s1", "s5", "s6", "s10", "s16", "s18", "s19"]

# Raw CMAPSS column layout.
RAW_COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]
OP_COLS = ["op1", "op2", "op3"]


def kept_sensor_cols() -> list[str]:
    """Sensor columns kept after dropping near-zero-variance ones, in order."""
    return [f"s{i}" for i in range(1, 22) if f"s{i}" not in DROP_SENSORS]


def feature_columns(sensor_cols: list[str] | None = None) -> list[str]:
    """The full ordered feature list the model expects."""
    sensor_cols = sensor_cols if sensor_cols is not None else kept_sensor_cols()
    return (
        OP_COLS
        + sensor_cols
        + [f"{c}_mean{WINDOW}" for c in sensor_cols]
        + [f"{c}_std{WINDOW}" for c in sensor_cols]
    )


def _roll_std(vals: list[float]) -> float:
    """Rolling std matching pandas .rolling(min_periods=1).std() (ddof=1, NaN→0)."""
    return float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0


def add_rolling_features(df: pd.DataFrame, sensor_cols: list[str],
                         window: int = WINDOW) -> pd.DataFrame:
    """Offline (training) path: add `{s}_mean{W}` / `{s}_std{W}` per unit.

    Trailing window including the current cycle; partial windows allowed via
    `min_periods=1`; std NaN (single point) filled with 0.
    """
    grp = df.groupby("unit")
    for col in sensor_cols:
        df[f"{col}_mean{window}"] = grp[col].transform(
            lambda x: x.rolling(window, min_periods=1).mean()
        )
        df[f"{col}_std{window}"] = grp[col].transform(
            lambda x: x.rolling(window, min_periods=1).std().fillna(0)
        )
    return df


def build_feature_row(window_rows: list[dict], sensor_cols: list[str],
                      op_cols: list[str] = OP_COLS, window: int = WINDOW) -> dict:
    """Online (serving) path: build one feature dict from a trailing window.

    `window_rows` is the trailing window of raw row dicts *including the current
    cycle as the last element*. It must already be trimmed to at most `window`
    rows (e.g. a `deque(maxlen=window)`), so cycle i sees the same trailing
    cycles training would have seen. Produces values identical to
    `add_rolling_features` for the corresponding cycle.
    """
    current = window_rows[-1]
    feat = {op: current[op] for op in op_cols}
    for s in sensor_cols:
        vals = [r[s] for r in window_rows]
        feat[s] = current[s]
        feat[f"{s}_mean{window}"] = float(np.mean(vals))
        feat[f"{s}_std{window}"] = _roll_std(vals)
    return feat
