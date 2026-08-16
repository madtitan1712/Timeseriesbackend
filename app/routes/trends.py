from fastapi import APIRouter, Query
from app.schemas.trends import TrendsOverviewResponse
from app.services.trends_service import get_trends_overview

router = APIRouter()

@router.get("/trends/overview", response_model=TrendsOverviewResponse)
def get_trends(granularity: str = Query("monthly", description="Data granularity")):
    """Home page aggregate data and computed movers."""
    return get_trends_overview(granularity)