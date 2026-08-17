from fastapi import APIRouter, HTTPException, Query

from app.services.recommendations_service import (
    get_category_recommendations,
    get_portfolio_recommendations,
)

router = APIRouter()


@router.get("/recommendations/portfolio")
def portfolio_recommendations(
    granularity: str = Query("monthly", description="daily|weekly|monthly"),
):
    """Return ranked portfolio recommendations for the selected granularity."""
    if granularity not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="Granularity must be one of daily, weekly, monthly.")
    return get_portfolio_recommendations(granularity=granularity)


@router.get("/recommendations/category/{category}")
def category_recommendations(
    category: str,
    granularity: str = Query("monthly", description="daily|weekly|monthly"),
    horizon: int = Query(12, ge=1, le=24),
):
    """Return primary and secondary recommendations for a category."""
    if granularity not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="Granularity must be one of daily, weekly, monthly.")
    try:
        return get_category_recommendations(category=category, granularity=granularity, horizon=horizon)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
