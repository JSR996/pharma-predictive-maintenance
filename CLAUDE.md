# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# PharmaGuard — Predictive Maintenance Platform

Full-stack predictive maintenance system for pharma manufacturing equipment. ML trained on the
NASA CMAPSS turbofan dataset (RUL prediction + anomaly detection), a FastAPI backend that streams
live simulated sensor data over WebSocket, and a React dashboard with real-time charts, RUL gauges,
and an alert feed.

## Stack
- **Backend**: Python 3.11, FastAPI, scikit-learn, pandas, numpy, joblib, websockets, uvicorn
- **Frontend**: React 18, Vite, Recharts, Tailwind CSS
- **ML**: RandomForestRegressor (RUL), IsolationForest (anomaly), NASA CMAPSS FD001

## Key Commands
```bash
# Data → must run before training; downloads CMAPSS into backend/data/
python scripts/download_data.py

# Backend
cd backend && pip install -r requirements.txt
python model/train.py                       # Train + write backend/model/model.pkl
uvicorn main:app --reload --port 8000        # API + WS; docs at /docs

# Frontend
cd frontend && npm install
npm run dev                                  # http://localhost:5173
npm run build                                # production build

# Backend tests (pytest; config in backend/pytest.ini → testpaths=tests, pythonpath=.)
cd backend && pytest                                       # all 24 tests
cd backend && pytest tests/test_feature_parity.py          # one file
cd backend && pytest tests/test_routers.py::test_health    # one test
```
The backend has a pytest suite (`backend/tests/`, 24 tests) guarding specific
invariants — train/serve feature parity, conformal calibration, anomaly
calibration, router behavior, and streaming. There is no frontend unit-test
runner, no linter config, and no CI. Frontend E2E specs live in `frontend/tests/`
and are exercised ad hoc via the Playwright MCP server (see Tooling Conventions).

## Architecture — the one thing to understand

**The trained model drives the live dashboard.** [backend/simulator.py](backend/simulator.py)
runs in one of two modes, chosen automatically at import by `_build_simulators()`:

- **MODEL mode** (default — when `model.pkl` **and** `backend/data/test_FD001.txt` exist): each of
  the 5 equipment units is a `ModelReplaySimulator` that *replays a real CMAPSS engine run*. Every
  tick it reads that engine's raw row (op settings + sensors), maintains a live 10-cycle rolling
  window, builds the full feature vector the model expects, and calls `predict_rul()` — so the
  `rul_predicted` / `anomaly_score` / `status` on screen are the model's **actual predictions** on
  real sensor data. The CMAPSS sensors are linearly mapped onto the 5 pharma sensor names
  (`DISPLAY_MAP`) purely for display. **Sticky failure:** when an engine reaches end-of-run it is
  *held* at the failed state (RUL≈0, critical) until an operator performs maintenance —
  `POST /equipment/{id}/replace` (→ `replace_unit` → `sim.replace()`) swaps in a fresh healthy engine.
  It does not auto-respawn. Each reading carries a `failed` flag distinguishing "dead, awaiting
  service" from "still running but critical".
- **SYNTH mode** (fallback — model/data missing): the original `EquipmentSimulator` hand-tuned
  degradation curves, so `uvicorn` still runs before you've trained. `GET /health` reports which
  mode is active via `stream_mode`.

**Single producer.** A lone background task `tick_loop()` (started from the FastAPI `lifespan` in
[main.py](backend/main.py)) advances all simulators once per `TICK_INTERVAL` (1.5s) and stores
`_latest_snapshot`. WebSocket clients only *broadcast* that snapshot — they never tick — so the sim
advances at one fixed rate no matter how many browsers connect. `/equipment` and `/alerts` also read
`_latest_snapshot`, so REST and WS never disagree.

`model.pkl` is a dict bundle loaded once (cached via `lru_cache`) by
[backend/model/predict.py](backend/model/predict.py):
`{rf_model, iso_model, scaler, feature_cols, rul_cap, metrics, feature_importances}`. The same
`predict_rul()` also backs `POST /predict/` and `GET /predict/model-info`. Status thresholds live in
one place (`predict_rul`: critical `rul<20`, warning `rul<50`) and govern both the stream and REST.

**Frontend data flow.** [frontend/src/hooks/useWebSocket.js](frontend/src/hooks/useWebSocket.js) is
the single source of live state: it parses the WS array into `readings` (latest snapshot),
`history` (last 60 readings per equipment id, ~90s), and a deduped `alerts` list, and auto-reconnects
after 3s on close. REST helpers live in [frontend/src/utils/api.js](frontend/src/utils/api.js); note
every REST path keeps its **trailing slash** (`/equipment/`, `/alerts/`, `/predict/`) to match the
FastAPI router prefixes.

## ML Training Pipeline
[backend/model/train.py](backend/model/train.py) on CMAPSS FD001:
- Drops near-zero-variance sensors `s1,s5,s6,s10,s16,s18,s19`.
- RUL = `max_cycle - cycle`, **capped at 125** (standard CMAPSS preprocessing — degradation only
  meaningful near failure).
- Adds rolling mean + std over a 10-cycle window, per `unit`. **Feature engineering is centralized
  in [backend/model/features.py](backend/model/features.py)** — the single source of truth for
  `WINDOW`, `DROP_SENSORS`, and the feature columns. Both the offline path (`add_rolling_features`,
  used by `train.py`) and the live serving path (`build_feature_row`, used by `simulator.py`) import
  from it, so the two cannot drift; `tests/test_feature_parity.py` asserts they produce identical
  vectors cycle-by-cycle (including partial windows at the start of a run). Edit `features.py`, never
  the two call sites independently.
- `MinMaxScaler` → `RandomForestRegressor(n_estimators=200, max_depth=20, min_samples_split=5)` for
  RUL.
- **Anomaly = departure from healthy operation.** `IsolationForest` is trained on the *healthy
  regime only* (capped-RUL plateau), not all cycles, so it doesn't just re-flag degradation. Its
  `decision_function` distribution over healthy data is saved in the bundle (`anomaly_ref_scores`,
  `anomaly_quantile`); at inference `predict_rul` turns a live score into a real percentile against
  that baseline (no magic sigmoid). `is_anomaly` fires in the bottom `1-anomaly_quantile` tail
  (default 5%); `anomaly_score` is folded at the healthy median so typical healthy reads ~0 and rises
  to 1 toward failure.
- **Split by engine unit** with `GroupShuffleSplit` (15% of units held out), NOT a random row split.
  A row split leaks, because rolling-window features make consecutive cycles of one engine nearly
  identical — that's what inflated the old reported R². Honest eval lands around **RMSE ~17.5,
  R² ~0.82**. Requires `backend/data/train_FD001.txt`.

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Status, whether model.pkl exists, and active `stream_mode` (model/synth) |
| GET | /equipment/ | All equipment snapshot from simulators |
| GET | /equipment/{id} | Single equipment (404 if unknown) |
| POST | /equipment/{id}/replace | Operator maintenance: reset a unit to a fresh healthy engine (404 if unknown) |
| GET | /alerts/?limit=20 | Deterministic snapshot-derived alerts, sorted by severity |
| POST | /predict/ | ML RUL + calibrated conformal interval (`rul_low`/`rul_high`/`rul_interval`); 503 if model.pkl missing |
| GET | /predict/model-info | Model metrics + top feature importances |
| POST | /admin/reload | Hot-reload model.pkl + stream mode without restart (clears `load_bundle` cache, rebuilds simulators) |
| GET/POST | /admin/fault-injection | Read/toggle live fault injection in MODEL mode |
| WS | /ws/sensors | Live stream, JSON array of all equipment, ~1.5s |

CORS defaults to `localhost:5173` / `localhost:3000` (override via `PHARMAGUARD_CORS_ORIGINS`). The
`/admin/*` endpoints are gated by an optional `PHARMAGUARD_ADMIN_TOKEN` (`X-Admin-Token` header; open
when unset). Fault injection can also be enabled at startup via `PHARMAGUARD_FAULT_INJECTION`.

**Conformal intervals:** `train.py` stores `conformal_q` = 90th-percentile absolute residual on the
group-split val set; `predict_rul` returns `rul ± conformal_q` as a calibrated ~90% interval — real
predictive uncertainty, distinct from `ensemble_agreement` (tree consensus only). Keep `CONFORMAL_ALPHA`
(train) and the interval read (predict) in sync.

**Hot-reload & fault injection** live in [backend/simulator.py](backend/simulator.py):
`reload_simulators()` reassigns module-level `_simulators`/`MODE`; `set_fault_injection()` toggles
`_fault_cfg`, and `ModelReplaySimulator.tick()` perturbs a **copy** of the replay row (never the shared
bank) so injected spikes pass through the real model.

## Equipment (simulated)
COMP-01 Tablet Compression · COMP-02 Capsule Filling · COMP-03 Fluid Bed Dryer ·
COMP-04 Blister Packaging · COMP-05 HVAC Air Handler.

## Design System
Clean white-and-blue clinical/pharma theme (light). Tokens live in
[frontend/tailwind.config.js](frontend/tailwind.config.js); hardcoded SVG/Recharts hex mirrors them.
- **Background** `#EEF4FB` (blue-tinted cleanroom page) · **Surface** `#FFFFFF` / `#F1F5FB`
  (inner fill: pills, tracks, badges) · **Border** `#DBE7F3`
- **Brand accent** `#1D4ED8` (pharma blue — token `brand`; UI/brand only: header, focus rings,
  selected state, primary buttons, "Live" pill, info alerts)
- **Status** green/amber/red per clinical convention: **Normal** `#16A34A` · **Warning** `#B45309`
  (text token; graphics — RUL arc, meter, chart line — use the brighter `#D97706`, which clears the
  3:1 graphical bar) · **Critical** `#DC2626`. A *healthy fleet reads green, not blue* — brand blue
  is never a status color. All text tokens meet WCAG AA on white.
- **Ink** `#12233B` (text) · `#5B7089` (subtext)
- **Display font** Space Grotesk · **Body** Inter · **Mono** JetBrains Mono
- **Depth** soft neutral `shadow-sm` on cards — **no neon glows, no glassmorphism**.
- **Signature element**: RUL gauge rendered as a degradation arc, not a percentage bar.


## Tooling Conventions

### Design — Impeccable
This project uses the Impeccable skill pack for frontend work.
- Run `/impeccable critique` on any new component before considering it done
- Run `/impeccable polish` before committing UI changes
- The design system is non-negotiable: blue-tinted white (#EEF4FB) page, white cards,
  brand blue accent (#1D4ED8), green/amber/red status (#16A34A/#D97706/#DC2626),
  Space Grotesk display, Inter body. No purple, no gradients, no nested cards,
  no neon glows, no glassmorphism, no generic dashboard tropes. Brand blue is a
  UI accent only — never a status color (healthy reads green).
- The RULGauge degradation arc is the signature element — do not replace it
  with a percentage bar, even if asked to "simplify".

### Testing — Playwright MCP
This project uses the Playwright MCP server for browser automation.
- Use `playwright mcp` to self-QA changes against the running dev server
  (frontend on localhost:5173, backend on localhost:8000)
- E2E test specs live in `frontend/tests/`
- Before claiming a UI feature is "done", verify it through Playwright MCP
- Default to ARIA snapshots over coordinate-based clicks

### Quality bar
- All new UI must pass `/impeccable critique` with no findings
- All new flows must have a Playwright spec or at least a self-QA pass
- Never install a dependency for something a few lines of native code can do