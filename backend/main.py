"""
PharmaGuard Backend — FastAPI entry point.
Run: uvicorn main:app --reload --port 8000
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from routers import equipment, alerts, predict as predict_router
from simulator import stream_sensors, tick_loop

TICK_INTERVAL = 1.5  # seconds between simulation steps


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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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
    import os
    from simulator import MODE
    model_ready = os.path.exists(
        os.path.join(os.path.dirname(__file__), "model", "model.pkl")
    )
    return {
        "status": "ok",
        "model_loaded": model_ready,
        "stream_mode": MODE,   # "model" = predictions drive the dashboard
        "version": "1.0.0",
    }


# ── WebSocket — live sensor stream ───────────────────────────────────────────
@app.websocket("/ws/sensors")
async def sensor_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        await stream_sensors(websocket, interval=1.5)
    except WebSocketDisconnect:
        pass
