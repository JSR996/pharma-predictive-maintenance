from fastapi import APIRouter, HTTPException
from simulator import get_all_equipment_status, replace_unit

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("/")
def list_equipment():
    return {"equipment": get_all_equipment_status()}


@router.get("/{equipment_id}")
def get_equipment(equipment_id: str):
    all_eq = get_all_equipment_status()
    match = next((e for e in all_eq if e["id"] == equipment_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")
    return match


@router.post("/{equipment_id}/replace")
def replace_equipment(equipment_id: str):
    """Operator maintenance action: reset a unit to a fresh, healthy engine."""
    try:
        reading = replace_unit(equipment_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")
    return {"status": "replaced", "equipment_id": equipment_id, "reading": reading}
