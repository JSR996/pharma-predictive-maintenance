"""
Live sensor stream for 5 pharma equipment units.

Two modes, selected automatically at startup:

* MODEL mode (default when model.pkl + backend/data/test_FD001.txt exist):
  each equipment unit "replays" a real NASA CMAPSS engine run. On every tick we
  feed that engine's raw readings (op settings + sensors) plus a live 10-cycle
  rolling window through the trained model, so the RUL / anomaly / status shown on
  the dashboard are the model's actual predictions. The CMAPSS sensors are mapped
  onto the 5 pharma sensor names (temperature, pressure, ...) purely for display.

* SYNTH mode (fallback when the model or data is missing): the original hand-tuned
  degradation simulator, so `uvicorn` still runs out of the box before training.

When an engine reaches the end of its run it is "replaced" with a fresh engine, so
the stream loops forever instead of pinning every unit at RUL 0.
"""

import asyncio
import json
import os
import random
import re
from collections import deque
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

EQUIPMENT = [
    {"id": "COMP-01", "name": "Tablet Compression Machine", "unit": 1},
    {"id": "COMP-02", "name": "Capsule Filling Machine",    "unit": 2},
    {"id": "COMP-03", "name": "Fluid Bed Dryer",            "unit": 3},
    {"id": "COMP-04", "name": "Blister Packaging Unit",     "unit": 4},
    {"id": "COMP-05", "name": "HVAC Air Handler Unit",      "unit": 5},
]

# Sensor baseline ranges (realistic pharma manufacturing ranges) — used for the
# synthetic fallback and as the display target range when mapping CMAPSS sensors.
SENSOR_RANGES = {
    "temperature":  (55.0,  95.0),   # °C
    "pressure":     (10.0,  20.0),   # bar
    "vibration":    (0.1,   2.5),    # mm/s RMS
    "rpm":          (2800,  3600),   # RPM
    "flow_rate":    (30.0,  70.0),   # L/min
}

RUL_CAP = 125
WINDOW = 10               # rolling window, must match model/train.py
ANOMALY_PROB = 0.04       # synthetic fallback only

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "test_FD001.txt")
CMAPSS_COLS = ["unit", "cycle", "op1", "op2", "op3"] + [f"s{i}" for i in range(1, 22)]

# Which CMAPSS sensor drives each pharma display sensor (cosmetic mapping only).
DISPLAY_MAP = {
    "temperature": "s2",   # rises with degradation
    "pressure":    "s7",   # falls with degradation
    "vibration":   "s4",   # rises — top predictive feature
    "rpm":         "s9",
    "flow_rate":   "s12",  # falls with degradation
}

# Trained model is optional at import time; fall back to synthetic if unavailable.
try:
    from model.predict import predict_rul as _predict_rul
except Exception:
    _predict_rul = None


# ── Synthetic fallback simulator ─────────────────────────────────────────────
class EquipmentSimulator:
    """Hand-tuned degradation curves. Display only — does not use the model."""

    def __init__(self, equip: dict):
        self.id = equip["id"]
        self.name = equip["name"]
        self.unit = equip["unit"]
        self.cycle = random.randint(0, 60)
        self.max_cycles = RUL_CAP + random.randint(0, 40)
        self._last_anomaly = False

    def _replace(self) -> None:
        """Simulate a maintenance swap: failed unit is restored to healthy."""
        self.cycle = 0
        self.max_cycles = RUL_CAP + random.randint(0, 40)
        self._last_anomaly = False

    @property
    def rul(self) -> float:
        raw = self.max_cycles - self.cycle
        return max(0.0, min(float(raw), float(RUL_CAP)))

    @property
    def degradation(self) -> float:
        """0 = healthy, 1 = about to fail"""
        return min(1.0, self.cycle / self.max_cycles)

    def _sensor_value(self, key: str, is_anomaly: bool) -> float:
        lo, hi = SENSOR_RANGES[key]
        mid = (lo + hi) / 2
        span = (hi - lo) / 2

        if key in ("temperature", "vibration"):
            drift = self.degradation * span * 0.7
        elif key in ("pressure", "flow_rate"):
            drift = -self.degradation * span * 0.4
        else:
            drift = 0.0

        base = mid + drift
        noise = random.gauss(0, span * 0.06)
        value = base + noise
        if is_anomaly:
            spike = random.uniform(span * 0.4, span * 0.8) * random.choice([-1, 1])
            value += spike
        return round(max(lo * 0.9, min(value, hi * 1.1)), 2)

    def tick(self) -> dict[str, Any]:
        # End-of-life → replace, so the demo loops instead of rotting.
        if self.cycle >= self.max_cycles:
            self._replace()
        self.cycle += 1
        is_anomaly = random.random() < ANOMALY_PROB or (self.rul < 15 and random.random() < 0.35)
        self._last_anomaly = is_anomaly

        sensors = {k: self._sensor_value(k, is_anomaly) for k in SENSOR_RANGES}
        anomaly_score = round(self.degradation * 0.6 + (0.4 if is_anomaly else 0.0) + random.uniform(0, 0.05), 3)

        if is_anomaly or self.rul < 15:
            status = "critical"
        elif self.rul < 40:
            status = "warning"
        else:
            status = "normal"

        return {
            "equipment_id":   self.id,
            "equipment_name": self.name,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "sensors":        sensors,
            "rul_predicted":  round(self.rul, 1),
            "anomaly_score":  min(anomaly_score, 1.0),
            "is_anomaly":     is_anomaly,
            "status":         status,
            "cycle":          self.cycle,
            "degradation_pct": round(self.degradation * 100, 1),
        }


# ── Model-backed CMAPSS replay simulator ─────────────────────────────────────
class ModelReplaySimulator:
    """Replays a real CMAPSS engine run and predicts RUL/anomaly with the model."""

    def __init__(self, equip, bank, stats, raw_sensors, op_cols):
        self.id = equip["id"]
        self.name = equip["name"]
        self.bank = bank                # {engine_unit: [row_dict, ...]}
        self.stats = stats              # {sensor: (min, max)} for display scaling
        self.raw_sensors = raw_sensors  # e.g. ['s2','s3',...]
        self.op_cols = op_cols          # ['op1','op2','op3']
        self._assign_engine()

    def _assign_engine(self) -> None:
        self.engine_id = random.choice(list(self.bank.keys()))
        self.rows = self.bank[self.engine_id]
        # Stagger starting points across the whole run so the fleet boots with a
        # mix of healthy and near-failure units (varied RUL / status on screen).
        self.ptr = random.randint(0, max(1, len(self.rows) - 1))
        # Warm-start the rolling window from the cycles just before the start point
        # so the very first ticks have realistic mean/std features (avoids the model
        # seeing an out-of-distribution cold start and flagging false anomalies).
        self.window: deque = deque(self.rows[max(0, self.ptr - WINDOW):self.ptr],
                                   maxlen=WINDOW)

    def _build_features(self, row: dict) -> dict:
        feat = {op: row[op] for op in self.op_cols}
        for s in self.raw_sensors:
            feat[s] = row[s]
            vals = [r[s] for r in self.window]
            feat[f"{s}_mean{WINDOW}"] = float(np.mean(vals))
            # pandas rolling .std() uses ddof=1 and yields 0 for a single point
            feat[f"{s}_std{WINDOW}"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        return feat

    def _display_sensors(self, row: dict) -> dict:
        out = {}
        for pharma, cm in DISPLAY_MAP.items():
            lo_d, hi_d = SENSOR_RANGES[pharma]
            mn, mx = self.stats.get(cm, (0.0, 1.0))
            frac = (row[cm] - mn) / (mx - mn) if mx > mn else 0.5
            frac = max(0.0, min(1.0, frac))
            out[pharma] = round(lo_d + frac * (hi_d - lo_d), 2)
        return out

    def tick(self) -> dict[str, Any]:
        if self.ptr >= len(self.rows):
            self._assign_engine()       # engine reached end-of-run → replace
        row = self.rows[self.ptr]
        self.ptr += 1
        self.window.append(row)

        pred = _predict_rul(self._build_features(row))
        total = len(self.rows)
        degradation_pct = round(100 * self.ptr / total, 1)

        return {
            "equipment_id":   self.id,
            "equipment_name": self.name,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "sensors":        self._display_sensors(row),
            "rul_predicted":  pred["rul"],
            "anomaly_score":  pred["anomaly_score"],
            "is_anomaly":     pred["is_anomaly"],
            "status":         pred["status"],
            "cycle":          self.ptr,
            "degradation_pct": degradation_pct,
        }


# ── Mode selection ───────────────────────────────────────────────────────────
def _load_engine_bank(raw_sensors, op_cols):
    df = pd.read_csv(DATA_PATH, sep=r"\s+", header=None, names=CMAPSS_COLS)
    keep = op_cols + raw_sensors
    bank = {int(u): g.sort_values("cycle")[keep].to_dict("records")
            for u, g in df.groupby("unit")}
    stats = {s: (float(df[s].min()), float(df[s].max())) for s in raw_sensors}
    return bank, stats


def _build_simulators():
    """Returns (simulators, mode). Falls back to synthetic if model/data missing."""
    if _predict_rul is not None and os.path.exists(DATA_PATH):
        try:
            from model.predict import load_bundle
            feature_cols = load_bundle()["feature_cols"]
            raw_sensors = [c for c in feature_cols if re.fullmatch(r"s\d+", c)]
            op_cols = [c for c in feature_cols if re.fullmatch(r"op\d+", c)]
            bank, stats = _load_engine_bank(raw_sensors, op_cols)
            sims = {e["id"]: ModelReplaySimulator(e, bank, stats, raw_sensors, op_cols)
                    for e in EQUIPMENT}
            print(f"[simulator] MODEL mode — replaying CMAPSS through model.pkl "
                  f"({len(bank)} engines, {len(feature_cols)} features)")
            return sims, "model"
        except Exception as ex:  # pragma: no cover - defensive
            print(f"[simulator] model init failed ({ex}); using synthetic fallback")

    print("[simulator] SYNTH mode — model/data not found, using synthetic curves")
    return {e["id"]: EquipmentSimulator(e) for e in EQUIPMENT}, "synth"


_simulators, MODE = _build_simulators()

# Latest snapshot, produced by the single background tick loop and broadcast to
# every connected client. Ticking is decoupled from connections so the simulation
# advances at one fixed rate regardless of how many browsers are watching.
_latest_snapshot: list[dict] = []


def _prime_snapshot() -> list[dict]:
    global _latest_snapshot
    _latest_snapshot = [sim.tick() for sim in _simulators.values()]
    return _latest_snapshot


def get_all_equipment_status() -> list[dict]:
    """Snapshot for the REST /equipment and /alerts endpoints. Reads the same
    stream state the dashboard sees, so REST and WebSocket never disagree."""
    snap = _latest_snapshot or _prime_snapshot()
    return [{
        "id":             r["equipment_id"],
        "name":           r["equipment_name"],
        "rul":            r["rul_predicted"],
        "cycle":          r["cycle"],
        "status":         r["status"],
        "degradation_pct": r["degradation_pct"],
    } for r in snap]


async def tick_loop(interval: float = 1.5):
    """Single producer: advances ALL simulators one step every `interval` seconds
    and stores the result in `_latest_snapshot`. Started once at app startup, so the
    simulation runs at a fixed rate no matter how many WebSocket clients connect."""
    global _latest_snapshot
    while True:
        _latest_snapshot = [sim.tick() for sim in _simulators.values()]
        await asyncio.sleep(interval)


async def stream_sensors(websocket, interval: float = 1.5):
    """Consumer: broadcasts the latest snapshot to one client. Does NOT tick — it
    only reads the shared state produced by `tick_loop`."""
    try:
        while True:
            if _latest_snapshot:
                await websocket.send_text(json.dumps(_latest_snapshot))
            await asyncio.sleep(interval)
    except Exception:
        pass  # Client disconnected
