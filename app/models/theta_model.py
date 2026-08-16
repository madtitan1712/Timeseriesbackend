import numpy as np
import pandas as pd
from statsmodels.tsa.forecasting.theta import ThetaModel
from app.models.base import Forecaster, ForecastResult


class ThetaForecaster(Forecaster):
    name = "Theta"

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        # The ThetaModel requires a sufficient amount of history to calculate seasonality.
        # If history is extremely short, fallback to a simple naive approach.
        if len(history) < seasonal_period * 2:
            last_val = history[-1] if len(history) > 0 else 0.0
            return ForecastResult(values=[float(last_val)] * horizon)

        # Initialize and fit the Theta model
        # seasonal_period is passed directly to handle the daily/weekly seasonality correctly
        model = ThetaModel(history, period=seasonal_period)
        fitted_model = model.fit()

        # Generate point forecasts
        point_forecasts = fitted_model.forecast(horizon)

        # Extract 95% confidence intervals (alpha=0.05)
        # prediction_intervals returns a DataFrame with 'lower' and 'upper' columns
        intervals = fitted_model.prediction_intervals(steps=horizon, alpha=0.05)

        # Prevent lower bounds from dipping below zero (common in pharma sales)
        lower_bounds = np.maximum(0.0, intervals['lower']).tolist()
        upper_bounds = intervals['upper'].tolist()

        return ForecastResult(
            values=point_forecasts.tolist(),
            lower=lower_bounds,
            upper=upper_bounds
        )