from app.models.base import Forecaster
from app.models.baseline import SeasonalNaiveModel

# Cache is keyed by (category, granularity), not category alone — the same
# category can have a different best-performing model per granularity
# (confirmed empirically during this project's offline model validation),
# so the lookup and the cache both need the full pair as the key.
_MODEL_CACHE: dict[tuple[str, str], Forecaster] = {}
_BASELINE = SeasonalNaiveModel()

# TODO: replace with the real per-(category, granularity) mapping once the
# model-selection team's validated winners are available. Example shape:
#   _ASSIGNMENTS = {
#       ("M01AB", "monthly"): "chronos",
#       ("M01AB", "weekly"):  "auto_arima",
#       ("N02BA", "monthly"): "timesfm",
#       ...
#   }
_ASSIGNMENTS: dict[tuple[str, str], str] = {
    # Example placeholders — replace with real category names + granularities.
    ("CategoryA", "monthly"): "chronos",
    ("CategoryB", "monthly"): "timesfm",
}


def get_forecaster(category: str, granularity: str) -> Forecaster:
    """Returns the specific model assigned to a (category, granularity) pair.

    Falls back to SeasonalNaiveModel for any pair with no explicit
    assignment yet. Real models are lazily instantiated on first use and
    cached per (category, granularity) so a shared model (e.g. Chronos)
    isn't reloaded on every request, while still allowing different
    granularities of the same category to use different models.
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
    else:
        forecaster = _BASELINE

    _MODEL_CACHE[key] = forecaster
    return forecaster