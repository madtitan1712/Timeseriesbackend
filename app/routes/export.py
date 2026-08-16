import io
import csv
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.services.forecast_service import generate_forecast

router = APIRouter()


@router.get("/forecast/{category}/export.csv")
def export_forecast_csv(
        category: str,
        granularity: str = Query("monthly"),
        horizon: int = Query(12)
):
    """CSV export of the forecast data."""
    forecast_data = generate_forecast(category, granularity, horizon)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["period_step", "forecast_value", "lower_bound", "upper_bound"])

    for i, val in enumerate(forecast_data.values):
        lower = forecast_data.lower[i] if forecast_data.lower else ""
        upper = forecast_data.upper[i] if forecast_data.upper else ""
        writer.writerow([f"Step+{i + 1}", val, lower, upper])

    output.seek(0)

    headers = {
        "Content-Disposition": f"attachment; filename={category}_forecast_{granularity}.csv"
    }
    return StreamingResponse(output, media_type="text/csv", headers=headers)