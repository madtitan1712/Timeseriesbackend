from fastapi import APIRouter, Query
from app.schemas.diagnostics import DiagnosticsResponse
from app.services.diagnostics_service import compute_diagnostics

router = APIRouter()


@router.get("/categories/{category}/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics(category: str, granularity: str = Query("weekly")):
    """Diagnostics panel data, translating raw STL-decomposition metrics
    into plain language for the UI."""
    stats = compute_diagnostics(category, granularity)

    if stats["seasonal_strength"] is None:
        return DiagnosticsResponse(
            category=category,
            seasonality_strength="Unknown",
            volatility="Unknown",
            notes=stats["notes"],
        )

    seasonality_text = "Highly Seasonal" if stats["seasonal_strength"] > 0.7 else "Low Seasonality"
    volatility_text = "High Volatility" if stats["cv"] is not None and stats["cv"] > 1.0 else "Stable"

    return DiagnosticsResponse(
        category=category,
        seasonality_strength=seasonality_text,
        volatility=volatility_text,
        notes=stats["notes"],
    )