from app.data.loader import load_dataset
from app.schemas.freshness import FreshnessResponse


def get_freshness_data() -> FreshnessResponse:
    last_dates = {}
    notes = {}

    for gran in ["daily", "weekly", "monthly"]:
        df = load_dataset(gran)
        if not df.empty and 'datum' in df.columns:
            last_date = df['datum'].max().strftime('%Y-%m-%d')
            last_dates[gran] = last_date
            notes[gran] = "Data loaded successfully."
        else:
            last_dates[gran] = "N/A"
            notes[gran] = "Dataset missing or empty."

    return FreshnessResponse(last_dates=last_dates, notes=notes)