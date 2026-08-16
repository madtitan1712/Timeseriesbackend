from pydantic import BaseModel
from typing import Optional, List

class ForecastResponse(BaseModel):
    values: List[float]
    lower: Optional[List[float]] = None
    upper: Optional[List[float]] = None