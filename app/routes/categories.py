from fastapi import APIRouter, Query

from app.data.loader import get_categories

router = APIRouter()

AVAILABLE_GRANULARITIES = ["daily", "weekly", "monthly"]


@router.get("/categories")
def list_categories(granularity: str = Query("weekly", description="Data granularity")):
    """List categories for the given granularity, plus which granularities exist.

    Kept as an object (not a bare list) to match the response shape the
    original inline endpoint returned, so any frontend code already built
    against {"categories": [...], "granularities": [...]} doesn't break.
    """
    return {
        "categories": get_categories(granularity),
        "granularities": AVAILABLE_GRANULARITIES,
    }