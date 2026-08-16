from fastapi import APIRouter, Query
from typing import Dict
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import generate_forecast

router = APIRouter()


@router.get("/compare/forecasts", response_model=Dict[str, ForecastResponse])
def compare_forecasts(
        categories: str = Query(..., description="Comma-separated categories, e.g., M01AB,R03"),
        granularity: str = Query("monthly"),
        horizon: int = Query(12)
):
    """Multi-category overlay data."""
    cat_list = [c.strip() for c in categories.split(",")]
    results = {}

    for cat in cat_list:
        # Reuses the exact single-category forecast orchestration
        results[cat] = generate_forecast(cat, granularity, horizon)

    return results