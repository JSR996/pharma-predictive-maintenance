from fastapi import APIRouter
from simulator import get_all_equipment_status

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Deterministic message per severity, derived from the unit's real status/RUL —
# so /alerts/ tells the same story as the live WebSocket stream (no randomness).
ALERT_MESSAGES = {
    "critical": "RUL below critical threshold — {rul} cycles remaining, schedule immediate maintenance",
    "warning":  "RUL entering warning zone — {rul} cycles remaining, schedule inspection",
    "info":     "Operating within normal parameters — {rul} cycles remaining",
}


def _make_alerts(equipment: list[dict]) -> list[dict]:
    """One alert per unit, derived deterministically from the live snapshot.

    Same input snapshot → same output, so repeated calls are stable and the REST
    feed never contradicts the WebSocket-derived feed the dashboard renders.
    """
    alerts = []

    for eq in equipment:
        status = eq["status"]
        severity = status if status != "normal" else "info"
        alerts.append({
            "id":             f"ALT-{eq['id']}-{eq['cycle']}",
            "equipment_id":   eq["id"],
            "equipment_name": eq["name"],
            "severity":       severity,
            "message":        ALERT_MESSAGES[severity].format(rul=eq["rul"]),
            "rul":            eq["rul"],
            # Tied to the snapshot reading (not call time) so the same snapshot
            # always yields identical alerts and the times match the WS feed.
            "timestamp":      eq["timestamp"],
            "acknowledged":   False,
        })

    # Sort: critical first, then warning, then info.
    priority = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: priority[a["severity"]])
    return alerts


@router.get("/")
def get_alerts(limit: int = 20):
    equipment = get_all_equipment_status()
    alerts = _make_alerts(equipment)
    return {"alerts": alerts[:limit], "total": len(alerts)}
