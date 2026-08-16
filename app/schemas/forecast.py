from pydantic import BaseModel
from typing import List, Optional

class ForecastResponse(BaseModel):
    dates: List[str]
    values: List[float]
    lower: Optional[List[float]] = None
    upper: Optional[List[float]] = None