"""
Unit coverage for the REST surface (routers/* + the admin endpoints in main.py),
which were previously exercised only by the Playwright e2e suite. These run against
a TestClient in whatever stream mode is active (SYNTH needs no model.pkl), without
starting the background tick loop, so the snapshot stays stable across calls.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

# No `with` → lifespan/tick_loop does not start; endpoints prime the snapshot on
# demand, so repeated reads of the same snapshot are deterministic.
client = TestClient(app)


def test_health_reports_mode_and_model_flag():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "stream_mode" in body
    assert body["stream_mode"] in ("model", "synth")
    assert "model_loaded" in body


def test_equipment_list_and_single():
    r = client.get("/equipment/")
    assert r.status_code == 200
    eq = r.json()["equipment"]
    assert len(eq) == 5
    ids = {e["id"] for e in eq}
    assert "COMP-01" in ids

    one = client.get("/equipment/COMP-01")
    assert one.status_code == 200
    assert one.json()["id"] == "COMP-01"


def test_equipment_unknown_404():
    assert client.get("/equipment/NOPE").status_code == 404


def test_equipment_replace_resets_unit():
    r = client.post("/equipment/COMP-01/replace")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "replaced"
    assert body["equipment_id"] == "COMP-01"
    assert body["reading"]["failed"] is False


def test_equipment_replace_unknown_404():
    assert client.post("/equipment/NOPE/replace").status_code == 404


def test_alerts_shape_sorting_limit_and_determinism():
    r = client.get("/alerts/?limit=3")
    assert r.status_code == 200
    body = r.json()
    alerts = body["alerts"]
    assert len(alerts) <= 3

    valid = {"critical", "warning", "info"}
    assert all(a["severity"] in valid for a in alerts)

    # Sorted critical → warning → info.
    rank = {"critical": 0, "warning": 1, "info": 2}
    ranks = [rank[a["severity"]] for a in alerts]
    assert ranks == sorted(ranks)

    # Deterministic: same snapshot → identical payload.
    assert client.get("/alerts/?limit=3").json() == body


def test_predict_includes_conformal_interval_or_503():
    payload = {"equipment_id": "COMP-01", "sensors": {"s2": 642.0, "s3": 1590.0}}
    r = client.post("/predict/", json=payload)
    if r.status_code == 503:
        pytest.skip("model.pkl not present")
    assert r.status_code == 200
    body = r.json()
    assert "rul" in body and "status" in body
    # New calibrated-interval fields (present once the model is retrained).
    if "rul_low" in body:
        assert body["rul_low"] <= body["rul"] <= body["rul_high"]


def test_admin_reload_returns_stream_health():
    r = client.post("/admin/reload")
    assert r.status_code == 200
    assert "stream_mode" in r.json()


def test_admin_fault_injection_roundtrip():
    r = client.post("/admin/fault-injection",
                    json={"enabled": True, "prob": 0.3, "magnitude": 0.7})
    assert r.status_code == 200
    cfg = r.json()
    assert cfg["enabled"] is True
    assert cfg["prob"] == 0.3 and cfg["magnitude"] == 0.7
    assert client.get("/admin/fault-injection").json()["enabled"] is True

    # Reset so other tests/state aren't affected.
    client.post("/admin/fault-injection", json={"enabled": False})
