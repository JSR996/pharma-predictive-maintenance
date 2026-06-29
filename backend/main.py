"""
PharmaGuard Backend — FastAPI entry point.
Run: uvicorn main:app --reload --port 8000
"""

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from routers import equipment, alerts, predict as predict_router
from simulator import (
    stream_sensors, tick_loop, get_stream_health,
    reload_simulators, set_fault_injection, get_fault_injection,
)

TICK_INTERVAL = 1.5  # seconds between simulation steps

# Optional shared secret for the /admin/* endpoints. If set, callers must send a
# matching `X-Admin-Token` header; if unset, the endpoints are open (matching the
# existing CORS-gated, local-demo posture).
ADMIN_TOKEN = os.getenv("PHARMAGUARD_ADMIN_TOKEN", "").strip()


def _require_admin(x_admin_token: Optional[str]) -> None:
    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="invalid or missing admin token")

# CORS origins from env (comma-separated), defaulting to the local dev servers.
_DEFAULT_ORIGINS = "http://localhost:5173,http://localhost:3000"
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("PHARMAGUARD_CORS_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the single background simulation loop. All clients read its output.
    task = asyncio.create_task(tick_loop(interval=TICK_INTERVAL))
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    title="PharmaGuard API",
    description="Predictive Maintenance for Pharma Manufacturing Equipment",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(equipment.router)
app.include_router(alerts.router)
app.include_router(predict_router.router)


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health():
    model_ready = os.path.exists(
        os.path.join(os.path.dirname(__file__), "model", "model.pkl")
    )
    # Read stream liveness/mode live (not a stale import-time snapshot), so a
    # frozen producer or a mode change is observable here.
    return {
        "status": "ok",
        "model_loaded": model_ready,
        "version": "1.0.0",
        **get_stream_health(),   # stream_mode, last_tick, last_error, equipment_count
    }


# ── Admin — hot-reload & fault injection (no restart) ────────────────────────
class FaultInjectionPayload(BaseModel):
    enabled: bool
    prob: Optional[float] = None
    magnitude: Optional[float] = None


@app.post("/admin/reload", tags=["system"])
def admin_reload(x_admin_token: Optional[str] = Header(default=None)):
    """Reload model.pkl and rebuild simulators without restarting the process."""
    _require_admin(x_admin_token)
    return reload_simulators()


@app.post("/admin/fault-injection", tags=["system"])
def admin_fault_injection(
    payload: FaultInjectionPayload,
    x_admin_token: Optional[str] = Header(default=None),
):
    """Toggle/configure live fault injection in MODEL mode."""
    _require_admin(x_admin_token)
    return set_fault_injection(payload.enabled, payload.prob, payload.magnitude)


@app.get("/admin/fault-injection", tags=["system"])
def admin_fault_injection_status(x_admin_token: Optional[str] = Header(default=None)):
    _require_admin(x_admin_token)
    return get_fault_injection()


# ── WebSocket — live sensor stream ───────────────────────────────────────────
@app.websocket("/ws/sensors")
async def sensor_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        await stream_sensors(websocket, interval=1.5)
    except WebSocketDisconnect:
        pass
