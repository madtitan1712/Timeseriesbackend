from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends
import pandas as pd
from sqlalchemy import text
from app.core.config import settings
from app.data.database import engine
from app.data.loader import invalidate_data_cache
from app.services.trends_service import invalidate_trends_cache
from app.routes.auth import get_current_user

router = APIRouter(tags=["Data Upload"])


@router.post("/data/upload")
async def upload_sales_data(
        file: UploadFile = File(...),
        granularity: str = Query(..., description="daily, weekly, or monthly"),
        current_user: dict = Depends(get_current_user)  # Requires valid JWT
):
    if granularity not in {"daily", "weekly", "monthly"}:
        raise HTTPException(400, "granularity must be daily, weekly, or monthly")

    try:
        df = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(400, "Invalid CSV file format")

    df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
    if df["datum"].isna().any():
        raise HTTPException(400, "Unparseable dates found in the 'datum' column")

    # Filter for whitelisted categories configured in settings
    category_cols = [c for c in df.columns if c in settings.CATEGORY_COLUMNS]
    if not category_cols:
        raise HTTPException(400, "No recognized category columns found in upload")

    long_df = df.melt(id_vars=["datum"], value_vars=category_cols, var_name="category", value_name="value")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df = long_df.dropna(subset=["value"])
    long_df["granularity"] = granularity
    long_df = long_df.rename(columns={"datum": "date"})

    try:
        with engine.begin() as conn:
            for _, row in long_df.iterrows():
                conn.execute(
                    text("""
                         INSERT INTO sales (granularity, category, date, value)
                         VALUES (:g, :c, :d, :v) ON CONFLICT (granularity, category, date) 
                        DO
                         UPDATE SET value = EXCLUDED.value
                         """),
                    {
                        "g": row["granularity"],
                        "c": row["category"],
                        "d": row["date"],
                        "v": row["value"]
                    },
                )
    except Exception as e:
        raise HTTPException(500, f"Database transaction failed: {str(e)}")

    # Clean cache invalidation
    invalidate_data_cache(granularity)
    invalidate_trends_cache(granularity)

    return {
        "status": "success",
        "rows_inserted": len(long_df),
        "uploaded_by": current_user["email"]
    }