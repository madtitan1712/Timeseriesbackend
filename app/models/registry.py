from app.models.base import Forecaster
from app.models.baseline import SeasonalNaiveModel

_MODEL_CACHE: dict[str, Forecaster] = {}
_BASELINE = SeasonalNaiveModel()


def get_forecaster(category: str, granularity: str) -> Forecaster:
    """
    Returns the specific model assigned to a (category, granularity) pair.
    Implements lazy loading to save memory during startup.
    """

    # Example mapping: Assign Chronos to 'CategoryA' and TimesFM to 'CategoryB'
    if category == "CategoryA":
        if "chronos" not in _MODEL_CACHE:
            from app.models.chronos_model import ChronosModel
            _MODEL_CACHE["chronos"] = ChronosModel()
        return _MODEL_CACHE["chronos"]

    elif category == "CategoryB":
        if "timesfm" not in _MODEL_CACHE:
            from app.models.transformer_model import TimesFMModel
            # Note: you may need to adjust context_len based on granularity
            _MODEL_CACHE["timesfm"] = TimesFMModel()
        return _MODEL_CACHE["timesfm"]

    # Default fallback
    return _BASELINE