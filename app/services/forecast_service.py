import pandas as pd

from app.core.config import settings
from app.data.loader import get_category_history, load_dataset
from app.models.registry import get_forecaster
from app.schemas.forecast import ForecastResponse


def generate_forecast(category: str, granularity: str = "monthly", horizon: int = 12) -> ForecastResponse:
    history = get_category_history(category, granularity)

    if history.empty:
        raise ValueError(f"Category '{category}' not found for granularity '{granularity}'")

    forecaster = get_forecaster(category, granularity)
    seasonal_period = settings.SEASONAL_PERIODS.get(granularity, 12)

    # Every Forecaster implementation accepts the same three arguments —
    # models that don't need seasonal_period (e.g. Chronos) simply ignore
    # it. Keeping the call uniform here is what makes the registry able to
    # swap models per (category, granularity) without any special-casing.
    forecast_result = forecaster.predict(
        history=history.to_numpy(),
        horizon=horizon,
        seasonal_period=seasonal_period,
    )

    df = load_dataset(granularity)
    last_date = df["datum"].max()
    freq_map = {"monthly": "ME", "weekly": "W", "daily": "D"}
    freq = freq_map.get(granularity, "ME")

    future_dates = pd.date_range(start=last_date, periods=horizon + 1, freq=freq)[1:]
    future_dates_str = future_dates.strftime("%Y-%m-%d").tolist()

    return ForecastResponse(
        dates=future_dates_str,
        values=forecast_result.values,
        lower=forecast_result.lower,
        upper=forecast_result.upper,
    )