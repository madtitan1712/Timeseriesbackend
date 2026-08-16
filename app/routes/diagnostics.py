import os
import pandas as pd
from fastapi import APIRouter
from app.schemas.diagnostics import DiagnosticsResponse
from app.core.config import settings

router = APIRouter()


@router.get("/categories/{category}/diagnostics", response_model=DiagnosticsResponse)
def get_diagnostics(category: str):
    """Diagnostics panel data, translating raw metrics to plain language."""
    file_path = os.path.join(settings.DATA_DIR, "diagnostic_features.csv")

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        if category in df['category'].values:
            row = df[df['category'] == category].iloc[0]
            # Assumes your CSV has columns that map to these plain-language summaries
            return DiagnosticsResponse(
                category=category,
                seasonality_strength=str(row.get('seasonality', 'Unknown')),
                volatility=str(row.get('volatility', 'Unknown')),
                notes="Derived from diagnostic_features.csv"
            )

    # Mock fallback until the CSV is dropped into the raw data folder
    return DiagnosticsResponse(
        category=category,
        seasonality_strength="Highly Seasonal",
        volatility="Low Volatility",
        notes="Mocked data: diagnostic_features.csv not found."
    )