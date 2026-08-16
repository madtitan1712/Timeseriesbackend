from fastapi import APIRouter
from app.schemas.freshness import FreshnessResponse
from app.services.freshness_service import get_freshness_data

router = APIRouter()

@router.get("/data/freshness", response_model=FreshnessResponse)
def get_freshness():
    """Returns the last available data date per granularity."""
    return get_freshness_data()