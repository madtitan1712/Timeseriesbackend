# app/routes/compare.py
import logging
from fastapi import APIRouter, Query
from typing import Dict
from app.schemas.forecast import ForecastResponse
from app.services.forecast_service import generate_forecast

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/compare/forecasts", response_model=Dict[str, ForecastResponse])
def compare_forecasts(
        categories: str = Query(..., description="Comma-separated categories, e.g., M01AB,R03"),
        granularity: str = Query("weekly"),
        horizon: int = Query(12)
):
    """Multi-category overlay data. Categories that fail to forecast (missing
    model artifact, bad category name, etc.) are omitted from the response
    rather than failing the whole request — check the server logs if a
    category you expected is missing."""
    cat_list = [c.strip() for c in categories.split(",")]
    results = {}

    for cat in cat_list:
        try:
            # Reuses the exact single-category forecast orchestration
            results[cat] = generate_forecast(cat, granularity, horizon)
        except Exception as e:
            logger.warning(f"Skipping {cat}/{granularity} in compare_forecasts: {e}")
            continue

    return results