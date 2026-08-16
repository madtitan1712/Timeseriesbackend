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


settings = Settings()