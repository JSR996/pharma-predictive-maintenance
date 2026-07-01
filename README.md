# PharmaGuard — Predictive Maintenance Platform

> Real-time predictive maintenance for pharma manufacturing equipment, powered by ML trained on NASA CMAPSS data.

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Stack](https://img.shields.io/badge/stack-React%20%2B%20FastAPI%20%2B%20scikit--learn-blue)
![Dataset](https://img.shields.io/badge/dataset-NASA%20CMAPSS%20FD001-orange)

## Overview

PharmaGuard monitors 5 pharma equipment units in real-time, predicting **Remaining Useful Life (RUL)** and detecting anomalies before failures occur. Built as a portfolio project demonstrating production-grade ML + full-stack integration.

**Equipment monitored:**
- Tablet Compression Machine
- Capsule Filling Machine
- Fluid Bed Dryer
- Blister Packaging Unit
- HVAC Air Handler Unit

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  React Dashboard (Vite + Tailwind + Recharts)           │
│  - Real-time sensor charts via WebSocket                │
│  - RUL degradation arc gauges                           │
│  - Alert feed with severity levels                      │
└──────────────────────┬──────────────────────────────────┘
                       │ WS /ws/sensors + REST API
┌──────────────────────▼──────────────────────────────────┐
│  FastAPI Backend                                        │
│  - WebSocket: live sensor stream (1.5s interval)        │
│  - REST: /equipment, /alerts, /predict, /health         │
│  - Sensor Simulator: 5 units w/ degradation curves      │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  ML Models (scikit-learn)                               │
│  - RandomForestRegressor → RUL prediction               │
│  - IsolationForest → anomaly detection                  │
│  - Trained on NASA CMAPSS FD001                         │
└─────────────────────────────────────────────────────────┘
```

## Quickstart

### 1. Download Data
```bash
python scripts/download_data.py
# If auto-download fails, see manual instructions in the script
```

### 2. Train the Model
```bash
cd backend
pip install -r requirements.txt
python model/train.py
# Outputs: backend/model/model.pkl
# Expect: RMSE ~18-22, R² ~0.93+
```

### 3. Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Dashboard: http://localhost:5173
```

## ML Details

| Component | Details |
|-----------|---------|
| Dataset | NASA CMAPSS FD001 (single fault mode, sea-level ops) |
| Target | RUL in cycles, capped at 125 (standard preprocessing) |
| Features | 14 sensors + 3 op settings + rolling mean/std (10-cycle window) |
| RUL Model | `RandomForestRegressor(n_estimators=200, max_depth=20)` |
| Anomaly Model | `IsolationForest(contamination=0.05)` |
| Eval Metrics | RMSE, MAE, R² on 15% holdout |

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health + model status |
| `GET` | `/equipment/` | All equipment with current status |
| `GET` | `/equipment/{id}` | Single equipment detail |
| `GET` | `/alerts/` | Recent alerts by severity |
| `POST` | `/predict/` | Run RUL prediction on sensor payload |
| `GET` | `/predict/model-info` | Model metrics + feature importances |
| `WS` | `/ws/sensors` | Live sensor stream (JSON array, ~1.5s) |

### WebSocket Message Format
```json
[
  {
    "equipment_id": "COMP-01",
    "equipment_name": "Tablet Compression Machine",
    "timestamp": "2026-06-28T10:00:00+00:00",
    "sensors": {
      "temperature": 72.4,
      "pressure": 14.3,
      "vibration": 0.82,
      "rpm": 3200,
      "flow_rate": 45.2
    },
    "rul_predicted": 87.3,
    "anomaly_score": 0.12,
    "is_anomaly": false,
    "status": "normal",
    "cycle": 38,
    "degradation_pct": 30.4
  }
]
```

## Project Structure
```
pharma-predictive-maintenance/
├── backend/
│   ├── main.py              # FastAPI app + WebSocket
│   ├── simulator.py         # Live sensor degradation simulator
│   ├── model/
│   │   ├── train.py         # Training script
│   │   ├── predict.py       # Inference helpers
│   │   └── model.pkl        # Saved model (after training)
│   ├── routers/
│   │   ├── equipment.py
│   │   ├── alerts.py
│   │   └── predict.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # Dashboard, Charts, Gauges, Alerts
│       ├── hooks/           # useWebSocket
│       └── utils/           # API helpers
├── notebooks/
│   └── eda_and_training.ipynb
├── scripts/
│   └── download_data.py
└── CLAUDE.md                # Claude Code context
```

## Design

Dark navy dashboard (`#0A0E1A`) with teal accent (`#00D4AA`) — pharmaceutical cleanroom aesthetic. Signature element: RUL degradation arc gauge (not a percentage bar).

---

Built with React, FastAPI, scikit-learn, NASA CMAPSS dataset.
