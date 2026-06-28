from fastapi import APIRouter
from simulator import get_all_equipment_status

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("/")
def list_equipment():
    return {"equipment": get_all_equipment_status()}


@router.get("/{equipment_id}")
def get_equipment(equipment_id: str):
    all_eq = get_all_equipment_status()
    match = next((e for e in all_eq if e["id"] == equipment_id), None)
    if not match:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Equipment {equipment_id} not found")
    return match
