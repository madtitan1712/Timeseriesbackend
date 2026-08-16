from app.data.loader import get_category_history
from app.models.registry import get_forecaster
from app.schemas.forecast import ForecastResponse
from app.core.config import settings
import numpy as np


def generate_forecast(category: str, granularity: str, horizon: int) -> ForecastResponse:
    """Orchestrates the data fetching and model prediction for a single category."""

    # 1. Fetch history
    history_series = get_category_history(category, granularity)
    if history_series.empty:
        # Return zeros if the category doesn't exist to prevent hard crashes
        return ForecastResponse(values=[0.0] * horizon)

    history_array = history_series.to_numpy()

    # 2. Get the assigned model from the registry
    forecaster = get_forecaster(category, granularity)

    # 3. Lookup the seasonal period (e.g., 12 for monthly, 52 for weekly)
    seasonal_period = settings.SEASONAL_PERIODS.get(granularity, 12)

    # 4. Generate the prediction
    result = forecaster.predict(
        history=history_array,
        horizon=horizon,
        seasonal_period=seasonal_period
    )

    return ForecastResponse(
        values=result.values,
        lower=result.lower,
        upper=result.upper
    )