import numpy as np
from app.models.base import Forecaster, ForecastResult


class SeasonalNaiveModel(Forecaster):
    name = "Seasonal Naive"

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        if len(history) < seasonal_period:
            # Fallback to simple naive if history is too short
            last_val = history[-1] if len(history) > 0 else 0.0
            return ForecastResult(values=[float(last_val)] * horizon)

        # Repeat the last seasonal period
        last_season = history[-seasonal_period:]
        reps = (horizon // seasonal_period) + 1
        forecast_values = np.tile(last_season, reps)[:horizon]

        return ForecastResult(values=forecast_values.tolist())