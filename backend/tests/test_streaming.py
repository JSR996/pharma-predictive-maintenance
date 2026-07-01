"""
Unit coverage for the streaming producer and fault injection in simulator.py:
- `_tick_all` must isolate a failing simulator (reuse its last good reading) rather
  than dropping the whole snapshot.
- `_prime_snapshot` must yield one reading per equipment.
- Fault injection must perturb a *copy* of the replay row (never the shared bank)
  and only when enabled.
"""

import random

import pytest

import simulator
from simulator import (
    EQUIPMENT, ModelReplaySimulator, ANOMALY_PERSIST,
    _prime_snapshot, _tick_all, replace_unit, _bump_anomaly_streak,
    set_fault_injection, get_fault_injection,
)


def test_status_tiers_critical_only_when_stopped():
    from model.predict import status_for
    # CRITICAL is reserved for a stopped/failed machine (or no remaining life).
    assert status_for(0.0, False, failed=True) == "critical"
    assert status_for(0.0, False) == "critical"
    # A detected anomaly on a running unit is a WARNING, not critical.
    assert status_for(80.0, True) == "warning"
    # Low-but-nonzero RUL is a warning, not critical.
    assert status_for(15.0, False) == "warning"
    # Healthy.
    assert status_for(100.0, False) == "normal"


def test_anomaly_debounce_requires_persistence():
    # A one-off anomalous tick must not escalate.
    streak, eff = _bump_anomaly_streak(0, True)
    assert (streak, eff) == (1, False)

    # Escalates only once the streak reaches ANOMALY_PERSIST.
    streak, eff = 0, False
    for _ in range(ANOMALY_PERSIST):
        streak, eff = _bump_anomaly_streak(streak, True)
    assert streak == ANOMALY_PERSIST and eff is True

    # A normal tick resets the streak immediately.
    assert _bump_anomaly_streak(streak, False) == (0, False)


def test_prime_snapshot_one_reading_per_unit():
    snap = _prime_snapshot()
    assert len(snap) == len(EQUIPMENT)
    assert {r["equipment_id"] for r in snap} == {e["id"] for e in EQUIPMENT}


def test_tick_all_isolates_a_failing_sim(monkeypatch):
    # Seed last-good readings for every unit.
    _prime_snapshot()

    class Boom:
        def tick(self):
            raise RuntimeError("simulated tick failure")

    victim = next(iter(simulator._simulators))
    patched = dict(simulator._simulators)
    patched[victim] = Boom()
    monkeypatch.setattr(simulator, "_simulators", patched)

    snap = _tick_all()
    # Failing unit reused its last good reading; nobody dropped.
    assert len(snap) == len(EQUIPMENT)
    assert victim in {r["equipment_id"] for r in snap}
    assert simulator._last_error and victim in simulator._last_error


def _fake_replay_sim():
    equip = {"id": "T-01", "name": "Test", "unit": 1}
    # Include every CMAPSS sensor the display mapping reads (s2/s4/s7/s9/s12) so a
    # full tick() can run; values/stats are arbitrary — these tests check control
    # flow (sticky failure, copy-not-mutate), not prediction values.
    raw_sensors = sorted({cm for cm in simulator.DISPLAY_MAP.values()})
    rows = [{s: 5.0 for s in raw_sensors} | {"op1": 0.0} for _ in range(20)]
    bank = {1: rows}
    stats = {s: (0.0, 10.0) for s in raw_sensors}
    return ModelReplaySimulator(equip, bank, stats, raw_sensors, ["op1"]), rows


def test_fault_injection_perturbs_copy_not_bank():
    sim, rows = _fake_replay_sim()
    original = dict(rows[0])

    set_fault_injection(True, prob=1.0, magnitude=1.0)
    random.seed(0)
    out = sim._maybe_inject_fault(rows[0])

    assert out is not rows[0]            # a copy was returned
    assert out["s2"] != original["s2"]   # the value was perturbed
    assert rows[0] == original           # shared bank row untouched

    set_fault_injection(False)


def test_fault_injection_noop_when_disabled():
    sim, rows = _fake_replay_sim()
    set_fault_injection(False)
    assert sim._maybe_inject_fault(rows[0]) is rows[0]  # same object, untouched


def test_sticky_failure_holds_until_replaced():
    sim, rows = _fake_replay_sim()
    set_fault_injection(False)

    # Drive the engine to the end of its run.
    last = None
    for _ in range(len(rows) + 5):
        last = sim.tick()

    # Sticky: it failed and is HELD — it did not auto-respawn a new engine.
    assert last["failed"] is True
    assert sim._at_end is True
    # A held-failed unit reads unambiguously critical with an empty gauge.
    assert last["status"] == "critical"
    assert last["rul_predicted"] == 0.0
    eng_before, ptr_before = sim.engine_id, sim.ptr
    held = sim.tick()
    assert held["failed"] is True
    assert (sim.engine_id, sim.ptr) == (eng_before, ptr_before)  # frozen, no respawn

    # Manual maintenance brings it back healthy from the start of a fresh run.
    sim.replace()
    assert sim._at_end is False
    assert sim.ptr == 0
    fresh = sim.tick()
    assert fresh["failed"] is False


def test_replace_unit_patches_snapshot():
    _prime_snapshot()
    target = EQUIPMENT[0]["id"]
    reading = replace_unit(target)
    assert reading["equipment_id"] == target
    assert reading["failed"] is False
    # Snapshot now carries the fresh reading for that unit.
    snap_entry = next(r for r in simulator._latest_snapshot
                      if r["equipment_id"] == target)
    assert snap_entry["timestamp"] == reading["timestamp"]


def test_replace_unit_unknown_raises():
    with pytest.raises(KeyError):
        replace_unit("NOPE")
