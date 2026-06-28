from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/predict", tags=["predict"])


class SensorPayload(BaseModel):
    equipment_id: str
    sensors: dict[str, float]
    # Optional: pass pre-computed rolling features too
    extra_features: Optional[dict[str, float]] = None


@router.post("/")
def predict(payload: SensorPayload):
    try:
        from model.predict import predict_rul, get_feature_importances, get_model_metrics
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    features = {**payload.sensors}
    if payload.extra_features:
        features.update(payload.extra_features)

    result = predict_rul(features)
    return {
        "equipment_id": payload.equipment_id,
        **result,
    }


@router.get("/model-info")
def model_info():
    try:
        from model.predict import get_feature_importances, get_model_metrics
        return {
            "metrics": get_model_metrics(),
            "top_features": get_feature_importances(),
            "dataset": "NASA CMAPSS FD001",
            "algorithm": "RandomForestRegressor + IsolationForest",
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
