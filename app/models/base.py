from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
from pydantic import BaseModel

class ForecastResult(BaseModel):
    values: list[float]
    lower: Optional[list[float]] = None
    upper: Optional[list[float]] = None

class Forecaster(ABC):
    name: str

    @abstractmethod
    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        pass