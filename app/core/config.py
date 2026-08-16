import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Pharma Sales Dashboard API"
    # Points to backend/app/data/raw
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")

    # Seasonal periods based on granularity
    SEASONAL_PERIODS: dict[str, int] = {
        "daily": 7,
        "weekly": 52,
        "monthly": 12
    }

    # The canonical list of actual sellable drug categories.
    # Acts as a whitelist to ignore metadata columns (Year, Month, Hour, etc.)
    CATEGORY_COLUMNS: set[str] = {
        "M01AB", "M01AE", "N02BA", "N02BE", "N05B", "N05C", "R03", "R06"
    }


settings = Settings()