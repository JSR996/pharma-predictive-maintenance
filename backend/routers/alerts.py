import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from simulator import get_all_equipment_status

router = APIRouter(prefix="/alerts", tags=["alerts"])

ALERT_TEMPLATES = {
    "critical": [
        "RUL below critical threshold ({rul} cycles remaining)",
        "Anomaly spike detected — vibration exceeded safe range",
        "Temperature sensor reading critically high",
        "Imminent failure predicted within next 15 cycles",
    ],
    "warning": [
        "RUL entering warning zone ({rul} cycles remaining)",
        "Pressure trend declining — schedule inspection",
        "Vibration baseline drift detected over last 10 cycles",
        "Flow rate deviation — possible seal degradation",
    ],
    "info": [
        "Scheduled maintenance due in {rul} cycles",
        "Routine sensor calibration recommended",
        "Equipment operating within normal parameters",
    ],
}


def _make_alerts(equipment: list[dict]) -> list[dict]:
    alerts = []
    now = datetime.now(timezone.utc)

    for eq in equipment:
        status = eq["status"]
        if status == "normal" and random.random() > 0.3:
            continue  # Only ~30% of healthy equipment gets info alerts

        severity = status if status != "normal" else "info"
        templates = ALERT_TEMPLATES[severity]
        message = random.choice(templates).format(rul=eq["rul"])

        alerts.append({
            "id":           f"ALT-{eq['id']}-{int(now.timestamp())}",
            "equipment_id": eq["id"],
            "equipment_name": eq["name"],
            "severity":     severity,
            "message":      message,
            "rul":          eq["rul"],
            "timestamp":    (now - timedelta(seconds=random.randint(0, 300))).isoformat(),
            "acknowledged": False,
        })

    # Sort: critical first, then warning, then info; newest first within group
    priority = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: (priority[a["severity"]], a["timestamp"]), reverse=False)
    return alerts


@router.get("/")
def get_alerts(limit: int = 20):
    equipment = get_all_equipment_status()
    alerts = _make_alerts(equipment)
    return {"alerts": alerts[:limit], "total": len(alerts)}
