from app.models.base import Forecaster
from app.models.baseline import SeasonalNaiveModel

# Cache is keyed by (category, granularity), not category alone — the same
# category can have a different best-performing model per granularity
# (confirmed empirically during this project's offline model validation),
# so the lookup and the cache both need the full pair as the key.
_MODEL_CACHE: dict[tuple[str, str], Forecaster] = {}
_BASELINE = SeasonalNaiveModel()

# Assignments extracted directly from pharma_tier_and_model_architecture.xlsx
_ASSIGNMENTS: dict[tuple[str, str], str] = {
    # N02BE: Analgesics / Antipyretics (Paracetamol)
    ("N02BE", "daily"): "lightgbm",
    ("N02BE", "weekly"): "theta",

    # M01AB: Anti-inflammatory (Acetic acid derivatives)
    ("M01AB", "daily"): "lightgbm",
    ("M01AB", "weekly"): "lightgbm",

    # N02BA: Analgesics (Salicylic acid derivatives)
    ("N02BA", "daily"): "theta",
    ("N02BA", "weekly"): "timesfm",

    # N05B: Psycholeptics / Anxiolytics
    ("N05B", "daily"): "lightgbm",
    ("N05B", "weekly"): "timesfm",

    # M01AE: Anti-inflammatory (Propionic acid derivatives)
    ("M01AE", "daily"): "lightgbm",
    ("M01AE", "weekly"): "theta",

    # N05C: Hypnotics and Sedatives
    ("N05C", "daily"): "timesfm",
    ("N05C", "weekly"): "xgboost",

    # R03: Drugs for Obstructive Airway Diseases
    ("R03", "daily"): "timesfm",
    ("R03", "weekly"): "xgboost",

    # R06: Antihistamines for Systemic Use
    ("R06", "daily"): "lightgbm",
    ("R06", "weekly"): "lightgbm",
}


def get_forecaster(category: str, granularity: str) -> Forecaster:
    """Returns the specific model assigned to a (category, granularity) pair.

    Falls back to SeasonalNaiveModel for any pair with no explicit
    assignment yet. Real models are lazily instantiated on first use and
    cached per (category, granularity).
    """
    key = (category, granularity)

    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    model_id = _ASSIGNMENTS.get(key)

    if model_id == "chronos":
        from app.models.chronos_model import ChronosForecaster
        forecaster = ChronosForecaster()
    elif model_id == "timesfm":
        from app.models.transformer_model import TimesFMModel
        forecaster = TimesFMModel()
    elif model_id == "lightgbm":
        from app.models.lightgbm_model import LightGBMForecaster
        # Pass both category and granularity to load the exact joblib file
        forecaster = LightGBMForecaster(category=category, granularity=granularity)
    elif model_id == "theta":
        from app.models.theta_model import ThetaForecaster
        forecaster = ThetaForecaster()
    elif model_id == "xgboost":
        from app.models.xgboost_model import XGBoostForecaster
        # Only pass category; XGBoost handles weekly natively now
        forecaster = XGBoostForecaster(category=category)
    else:
        # Fallback for categories or granularities (e.g. monthly) not explicitly defined
        forecaster = _BASELINE

    _MODEL_CACHE[key] = forecaster
    return forecaster