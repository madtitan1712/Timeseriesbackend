from app.data.loader import get_categories, get_category_history, load_dataset
from app.services.forecast_service import generate_forecast
from app.models.registry import get_forecaster
from app.schemas.trends import TrendsOverviewResponse, MoverInfo, TotalTrend
import pandas as pd


def get_trends_overview(granularity: str = "monthly") -> TrendsOverviewResponse:
    categories = get_categories()
    category_trends = []

    # 1. Prepare historical dates and actuals
    df = load_dataset(granularity)
    if df.empty or 'datum' not in df.columns:
        return TrendsOverviewResponse(category_trends=[], needs_attention=[],
                                      total_trend=TotalTrend(dates=[], actuals=[], forecasts=[]))

    hist_dates = df['datum'].dt.strftime('%Y-%m-%d').tolist()
    total_actuals = [0.0] * len(hist_dates)

    # We will forecast 12 periods ahead for the total trend chart
    horizon = 12
    total_forecasts = [0.0] * horizon

    for cat in categories:
        history = get_category_history(cat, granularity)
        if history.empty:
            continue

        # Sum up historical actuals
        for i, val in enumerate(history.tolist()):
            if i < len(total_actuals):
                total_actuals[i] += val

        latest_actual = float(history.iloc[-1])

        # Grab the full horizon forecast
        forecast_res = generate_forecast(cat, granularity, horizon=horizon)

        # Sum up future forecasts across all categories
        for i, val in enumerate(forecast_res.values):
            if i < horizon:
                total_forecasts[i] += val

        next_forecast = float(forecast_res.values[0]) if forecast_res.values else 0.0

        pct_change = 0.0
        if latest_actual > 0:
            pct_change = ((next_forecast - latest_actual) / latest_actual) * 100

        forecaster = get_forecaster(cat, granularity)
        is_anomaly = abs(pct_change) > 20.0

        category_trends.append(
            MoverInfo(
                category=cat,
                latest_actual=latest_actual,
                next_forecast=next_forecast,
                percentage_change=pct_change,
                serving_model=forecaster.name,
                is_anomaly=is_anomaly
            )
        )

    needs_attention = sorted(category_trends, key=lambda x: abs(x.percentage_change), reverse=True)[:3]

    # 2. Generate future dates to append to the historical dates
    last_date = df['datum'].max()
    # Simple frequency mapping based on granularity
    freq_map = {"monthly": "ME", "weekly": "W", "daily": "D"}
    freq = freq_map.get(granularity, "ME")

    future_dates = pd.date_range(start=last_date, periods=horizon + 1, freq=freq)[1:]
    future_dates_str = future_dates.strftime('%Y-%m-%d').tolist()

    # 3. Combine history and future for the chart
    # We take the last 12 historical periods + the 12 future periods
    combined_dates = hist_dates[-12:] + future_dates_str

    # Actuals array: historical numbers + nulls for the future
    combined_actuals = total_actuals[-12:] + [None] * horizon

    # Forecast array: nulls for history + forecasted numbers for the future
    combined_forecasts = [None] * 12 + total_forecasts

    return TrendsOverviewResponse(
        category_trends=category_trends,
        needs_attention=needs_attention,
        total_trend=TotalTrend(
            dates=combined_dates,
            actuals=combined_actuals,
            forecasts=combined_forecasts
        )
    )