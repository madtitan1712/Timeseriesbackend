from fastapi import APIRouter, Query, HTTPException
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import generate_forecast

router = APIRouter()

@router.get("/forecast/{category}", response_model=ForecastResponse)
def get_forecast(category: str, granularity: str = Query("weekly"), horizon: int = Query(12)):
    try:
        return generate_forecast(category, granularity, horizon)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))