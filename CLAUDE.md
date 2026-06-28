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
```
There is no test suite, linter config, or CI in this repo.

## Architecture — the one thing to understand

**The trained model drives the live dashboard.** [backend/simulator.py](backend/simulator.py)
runs in one of two modes, chosen automatically at import by `_build_simulators()`:

- **MODEL mode** (default — when `model.pkl` **and** `backend/data/test_FD001.txt` exist): each of
  the 5 equipment units is a `ModelReplaySimulator` that *replays a real CMAPSS engine run*. Every
  tick it reads that engine's raw row (op settings + sensors), maintains a live 10-cycle rolling
  window, builds the full feature vector the model expects, and calls `predict_rul()` — so the
  `rul_predicted` / `anomaly_score` / `status` on screen are the model's **actual predictions** on
  real sensor data. The CMAPSS sensors are linearly mapped onto the 5 pharma sensor names
  (`DISPLAY_MAP`) purely for display. When an engine reaches end-of-run it is "replaced" with a new
  random engine, so the stream loops forever.
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
- Adds rolling mean + std over a 10-cycle window, per `unit` (`WINDOW` must stay in sync with the
  live window in `simulator.py`).
- `MinMaxScaler` → `RandomForestRegressor(n_estimators=200, max_depth=20, min_samples_split=5)` for
  RUL; `IsolationForest(contamination=0.05)` for anomaly.
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
| GET | /alerts/?limit=20 | Randomly-generated alerts, sorted by severity |
| POST | /predict/ | ML RUL prediction (503 if model.pkl missing) |
| GET | /predict/model-info | Model metrics + top feature importances |
| WS | /ws/sensors | Live stream, JSON array of all equipment, ~1.5s |

CORS is locked to `localhost:5173` and `localhost:3000`.

## Equipment (simulated)
COMP-01 Tablet Compression · COMP-02 Capsule Filling · COMP-03 Fluid Bed Dryer ·
COMP-04 Blister Packaging · COMP-05 HVAC Air Handler.

## Design System
- **Background** `#0A0E1A` (deep navy cleanroom) · **Surface** `#111827` / `#1F2937`
- **Accent** `#00D4AA` (teal-green) · **Critical** `#EF4444` · **Warning** `#F59E0B` · **Normal** `#00D4AA`
- **Display font** Space Grotesk · **Body** Inter
- **Signature element**: RUL gauge rendered as a degradation arc, not a percentage bar.
