from pydantic import BaseModel
from typing import List, Optional

class MoverInfo(BaseModel):
    category: str
    latest_actual: float
    next_forecast: float
    percentage_change: float
    serving_model: str
    is_anomaly: bool

class TotalTrend(BaseModel):
    dates: List[str]
    # Change this line: Wrap float in Optional so it accepts None for future dates
    actuals: List[Optional[float]]
    forecasts: List[Optional[float]]

class TrendsOverviewResponse(BaseModel):
    category_trends: List[MoverInfo]
    needs_attention: List[MoverInfo]
    total_trend: TotalTrend