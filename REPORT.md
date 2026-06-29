# PharmaGuard — Project Report

Predictive-maintenance platform for pharma manufacturing equipment. A machine-learning model
trained on the NASA CMAPSS turbofan dataset (RUL prediction + anomaly detection), served by a
FastAPI backend that streams live simulated sensor data over WebSocket, with a React dashboard
showing real-time charts, RUL gauges, and an alert feed.

_Last updated: 2026-06-29._

---

## 1. Project Structure

```
pharma-predictive-maintenance/
├── CLAUDE.md                 # Engineering guide / architecture notes (source of truth)
├── README.md, DESIGN.md, PRODUCT.md
├── REPORT.md                 # ← this file
├── .gitignore                # ignores node_modules, dist, *.pkl, data, .env, venvs
│
├── scripts/
│   └── download_data.py      # downloads CMAPSS FD001 into backend/data/
│
├── notebooks/
│   └── eda_and_training.ipynb# exploratory analysis + training walkthrough
│
├── backend/                  # Python 3.11 · FastAPI
│   ├── main.py               # app entry: lifespan tick loop, CORS, /health, WS route
│   ├── simulator.py          # live stream: MODEL-replay & SYNTH simulators, tick_loop
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── model/
│   │   ├── features.py       # SHARED feature engineering (train + serve) — single source
│   │   ├── train.py          # trains RF (RUL) + IsolationForest (anomaly) → model.pkl
│   │   ├── predict.py        # inference: predict_rul(), status_for(), anomaly calibration
│   │   └── model.pkl         # trained bundle (regenerated; gitignored)
│   ├── routers/
│   │   ├── equipment.py      # GET /equipment/, /equipment/{id}
│   │   ├── alerts.py         # GET /alerts/  (deterministic, snapshot-derived)
│   │   └── predict.py        # POST /predict/, GET /predict/model-info
│   ├── data/                 # CMAPSS *.txt (downloaded; gitignored)
│   └── tests/
│       ├── test_feature_parity.py      # train vs serve feature equality (#1)
│       └── test_anomaly_calibration.py # anomaly rises toward failure, 5% healthy flag (#2)
│
└── frontend/                 # React 18 · Vite · Tailwind · Recharts
    ├── src/
    │   ├── App.jsx
    │   ├── hooks/useWebSocket.js   # single source of live state (readings/history/alerts)
    │   ├── utils/api.js            # REST helpers (env-configurable base)
    │   └── components/             # Dashboard, EquipmentCard, RULGauge, SensorChart,
    │                               #   AlertFeed, Header
    ├── tests/dashboard.spec.js     # Playwright e2e (7 tests)
    ├── playwright.config.js
    └── .env.example                # VITE_API_BASE, VITE_WS_URL
```

**Stack:** FastAPI · scikit-learn · pandas/numpy · joblib · uvicorn (backend); React 18 · Vite ·
Recharts · Tailwind (frontend). **ML:** `RandomForestRegressor` (RUL) + `IsolationForest`
(anomaly) on CMAPSS FD001.

---

## 2. Pipeline (end to end)

```
download_data.py ─► CMAPSS FD001 ─► train.py ─► model.pkl
                                                   │
                                  (loaded once, lru_cache)
                                                   ▼
                       simulator.py: replay real engine + predict ──► tick_loop (1.5s)
                                                   │                        │
                                          _latest_snapshot ◄───────────────┘
                                          ╱        │        ╲
                                  /equipment/  /alerts/   WS /ws/sensors
                                                   │
                                          useWebSocket.js ─► React dashboard
```

1. **Data** — `scripts/download_data.py` fetches CMAPSS FD001 (`train/test_FD001.txt`) into
   `backend/data/`. Each row = one engine at one cycle: `unit, cycle, op1-3, s1-s21`.

2. **Feature engineering** (`model/features.py`, shared by train & serve) — drop 7 near-zero-variance
   sensors; add per-unit rolling **mean & std over a 10-cycle window** (trailing, `min_periods=1`).
   One implementation guarantees the training and live paths can never diverge.

3. **Training** (`model/train.py`) — label `RUL = max_cycle − cycle`, capped at 125. Split **by engine
   unit** (`GroupShuffleSplit`, 15% held out) to avoid leakage from near-identical windowed rows.
   `MinMaxScaler` → `RandomForestRegressor(200 trees)` for RUL; `IsolationForest` trained on the
   **healthy regime only** for anomaly, with its healthy `decision_function` distribution saved for
   calibration. Bundle (`model.pkl`) = `{rf_model, iso_model, scaler, feature_cols, rul_cap, metrics,
   feature_importances, anomaly_ref_scores, anomaly_quantile}`.

4. **Inference** (`model/predict.py`) — `predict_rul()` builds the feature vector, scales, predicts RUL
   (clamped 0–125), derives a calibrated anomaly score (real percentile vs healthy baseline; folded at
   the healthy median), and assigns status via the single `status_for()` rule (critical `rul<20` or
   anomaly; warning `rul<50`).

5. **Live simulation** (`simulator.py`) — auto-selects a mode at startup:
   - **MODEL mode** (model.pkl + data present): each of 5 equipment units replays a *real* CMAPSS
     engine. Every tick it reads the next raw row, maintains a live 10-cycle window, rebuilds the exact
     feature vector, and calls `predict_rul()` — so on-screen RUL/anomaly/status are the model's actual
     predictions. CMAPSS sensors are cosmetically mapped to pharma sensor names. End-of-run → a fresh
     random engine, so the stream loops.
   - **SYNTH mode** (fallback): hand-tuned degradation curves so `uvicorn` runs before training.

6. **Serving** (`main.py`) — a single background `tick_loop()` advances all simulators once per 1.5s
   and stores `_latest_snapshot`; it is hardened (per-sim failures isolated, never silently freezes) and
   reports liveness via `/health`. WebSocket clients only **broadcast** the snapshot (they never tick),
   so the sim runs at one fixed rate regardless of client count. `/equipment/` and `/alerts/` read the
   same snapshot, so REST and WS never disagree.

7. **Frontend** (`useWebSocket.js` → components) — single live-state hook parses the WS array into
   `readings` (latest), `history` (last 60 ≈ 90s per unit), and a deduped `alerts` list;
   auto-reconnects after 3s. Renders fleet status, equipment cards, sensor charts, RUL gauges, and the
   alert feed.

**Model performance (honest, group-split eval):** RMSE ≈ 17.5, MAE ≈ 12.3, R² ≈ 0.82. Top feature:
`s4_mean10` (a rolling sensor mean).

---

## 3. API Surface

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | status, `model_loaded`, live `stream_mode`, `last_tick`, `last_error`, `equipment_count` |
| GET | `/equipment/` | all-equipment snapshot |
| GET | `/equipment/{id}` | single unit (404 if unknown) |
| POST | `/equipment/{id}/replace` | operator maintenance — reset a unit to a fresh healthy engine (404 if unknown) |
| GET | `/alerts/?limit=20` | deterministic alerts derived from the live snapshot |
| POST | `/predict/` | ML RUL + anomaly + conformal interval (`rul_low`/`rul_high`/`rul_interval`); 503 if model missing |
| GET | `/predict/model-info` | metrics + top feature importances |
| POST | `/admin/reload` | hot-reload `model.pkl` + stream mode without restart |
| GET/POST | `/admin/fault-injection` | read / toggle live fault injection (MODEL mode) |
| WS | `/ws/sensors` | live stream, JSON array of all equipment, ~1.5s |

CORS origins are env-configurable (`PHARMAGUARD_CORS_ORIGINS`), default localhost:5173/3000. The
`/admin/*` endpoints are gated by an optional `PHARMAGUARD_ADMIN_TOKEN` (`X-Admin-Token` header);
fault injection can also be enabled at startup with `PHARMAGUARD_FAULT_INJECTION`.

---

## 4. Uses

- **Demo / reference architecture** for an end-to-end predictive-maintenance system: real ML driving a
  real-time dashboard, not a mockup.
- **RUL estimation** — surfaces remaining useful life per asset so maintenance is scheduled before
  failure rather than on a fixed calendar.
- **Anomaly detection** — flags readings that depart from healthy operation *independently of RUL*,
  catching unusual behavior before remaining life drops.
- **Fleet monitoring** — at-a-glance health of multiple assets (normal/warning/critical) with live
  sensor trends and an alert feed.
- **Teaching artifact** — clean examples of leakage-free time-series splitting, train/serve feature
  parity, calibrated anomaly scoring, single-producer streaming, and e2e testing.

---

## 5. Limitations

**Data / domain**
- The "pharma equipment" is **simulated** — it replays NASA turbofan (CMAPSS) engine runs. Sensor
  names (temperature, pressure, …) are a cosmetic mapping; this is not trained on real pharma data.
- CMAPSS FD001 is a single operating condition / single fault mode; the model would need retraining
  and revalidation on real plant telemetry before any production use.
- CMAPSS degradation is smooth, so the *unperturbed* live stream rarely shows sudden spikes. Optional
  **fault/noise injection** (`POST /admin/fault-injection`, or `PHARMAGUARD_FAULT_INJECTION`) now
  perturbs the replayed sensor rows *before* the model sees them, so injected spikes flow through the
  real prediction pipeline and surface as genuine `is_anomaly` flags — but the underlying data is still
  CMAPSS, not real pharma faults.

**Modeling**
- RUL is **capped at 125**, so the model does not distinguish "very healthy" assets (everything above
  the cap looks identical).
- Anomaly detection is an unsupervised `IsolationForest` baseline (no labeled fault data); it is now
  calibrated and honest but is not a fault classifier and does not identify *which* failure mode.
- `ensemble_agreement` measures tree consensus, **not** calibrated predictive uncertainty — don't read
  it as a probability. For real uncertainty, `/predict/` now also returns a **split-conformal interval**
  (`rul_low`/`rul_high`, ~90% coverage) calibrated on the held-out validation residuals.
- No temporal/sequence model (e.g. LSTM/Transformer) and no drift monitoring; rolling mean/std is the
  only temporal feature.

**System / operational**
- **Model & mode can now be hot-reloaded** via `POST /admin/reload` (clears the cached bundle, re-runs
  mode selection, re-primes the stream) — no process restart needed. The admin endpoints are gated by an
  optional `PHARMAGUARD_ADMIN_TOKEN` (open by default, matching the local-demo posture).
- Single-process, in-memory state (`_latest_snapshot`); no persistence, database, or history beyond the
  ~90s the frontend keeps. Not horizontally scalable as-is.
- No authentication/authorization; CORS-gated and intended for local/demo use.
- Alerts have no acknowledge/escalation workflow or notification delivery (email/SMS/etc.).
- `/alerts/` is now deterministic and snapshot-derived, but the dashboard still builds its own alerts
  from the WS stream; the REST endpoint is effectively a parallel (consistent) view, not the UI source.

**Testing**
- Backend unit coverage spans the ML invariants (feature parity, anomaly calibration, conformal
  intervals), the REST surface (`/health`, `/equipment`, `/alerts`, `/predict`, `/admin/*`), and the
  streaming producer (`_tick_all` failure isolation, fault injection). The Playwright e2e suite still
  covers the rendered dashboard end-to-end.

---

## 6. Health & Recent Hardening

This codebase was reviewed and 12 flaws were fixed (see
`~/.claude/plans/lets-do-all-in-stateful-lampson.md` for the full plan):

- **ML integrity** — unified train/serve feature engineering (+ parity test); `degradation_pct`
  derived from RUL; single status-threshold definition.
- **Anomaly detector (#2)** — retrained on the healthy regime with empirical percentile calibration
  (no magic constants); flags the bottom ~5% tail; score rises 0→1 toward failure.
- **Consistency** — `/alerts/` made deterministic and snapshot-derived.
- **Robustness** — `tick_loop` isolates per-sim failures and can't silently freeze; `/health` exposes
  liveness; specific WebSocket exception handling.
- **Production readiness** — `.gitignore` + untracked build artifacts; env-based frontend/CORS config;
  `confidence` renamed to `ensemble_agreement` with honest semantics.

**Verification status:** backend `pytest` 17/17 pass; Playwright 7/7 pass; RF metrics stable
(RMSE ≈ 17.5, R² ≈ 0.82, conformal ±30 cycles @90%); live stream shows anomaly scores low for healthy
units and rising toward failure, and fault injection drives genuine model-flagged anomalies.

**Recently closed (this pass):** hot-reload (`/admin/reload`), fault/noise injection
(`/admin/fault-injection`), calibrated conformal RUL intervals, and unit tests for the routers and
streaming producer.

### Suggested next steps
1. Validate on real pharma telemetry; revisit RUL cap and add fault-mode classification.
2. Persistence + alert acknowledge/notify workflow; auth before any non-local deployment.
3. Add a temporal model and drift monitoring for genuine real-time fault detection.
