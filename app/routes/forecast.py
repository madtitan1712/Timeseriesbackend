from fastapi import APIRouter, Query, HTTPException
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import generate_forecast

router = APIRouter()


@router.get("/forecast/{category}", response_model=ForecastResponse)
def get_forecast(
        category: str,
        granularity: str = Query("monthly", description="Data granularity: daily, weekly, monthly"),
        horizon: int = Query(12, description="Number of periods to forecast ahead")
):
    """Single-category forecast endpoint."""
    valid_granularities = ["daily", "weekly", "monthly"]
    if granularity not in valid_granularities:
        raise HTTPException(status_code=400, detail=f"Granularity must be one of {valid_granularities}")

    return generate_forecast(category, granularity, horizon)