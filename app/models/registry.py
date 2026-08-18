# app/models/registry.py
import logging
import threading
from app.models.base import Forecaster
from app.models.baseline import SeasonalNaiveModel

logger = logging.getLogger(__name__)

# Cache is keyed by (category, granularity), not category alone — the same
# category can have a different best-performing model per granularity
# (confirmed empirically during this project's offline model validation),
# so the lookup and the cache both need the full pair as the key.
_MODEL_CACHE: dict[tuple[str, str], Forecaster] = {}
_MODEL_CACHE_LOCK = threading.Lock()
_BASELINE = SeasonalNaiveModel()

# TimesFM is a zero-shot foundation model — it isn't fine-tuned per category,
# so the four (category, granularity) pairs assigned to it below all share
# ONE loaded instance instead of each paying their own ~200M-param load.
_TIMESFM_SINGLETON: Forecaster | None = None
_TIMESFM_LOCK = threading.Lock()

# Assignments extracted directly from pharma_tier_and_model_architecture.xlsx
_ASSIGNMENTS: dict[tuple[str, str], str] = {
    ("N02BE", "daily"): "lightgbm",
    ("N02BE", "weekly"): "theta",
    ("M01AB", "daily"): "lightgbm",
    ("M01AB", "weekly"): "lightgbm",
    ("N02BA", "daily"): "theta",
    ("N02BA", "weekly"): "timesfm",
    ("N05B", "daily"): "lightgbm",
    ("N05B", "weekly"): "timesfm",
    ("M01AE", "daily"): "lightgbm",
    ("M01AE", "weekly"): "theta",
    ("N05C", "daily"): "timesfm",
    ("N05C", "weekly"): "xgboost",
    ("R03", "daily"): "timesfm",
    ("R03", "weekly"): "xgboost",
    ("R06", "daily"): "lightgbm",
    ("R06", "weekly"): "lightgbm",
}


def _get_timesfm_instance() -> Forecaster:
    """Returns the single shared TimesFM instance, loading it on first call.

    Double-checked locking: the outer check avoids taking the lock on every
    call once warm, the inner check (after acquiring the lock) avoids two
    threads racing to load it simultaneously on cold start.
    """
    global _TIMESFM_SINGLETON

    if _TIMESFM_SINGLETON is not None:
        return _TIMESFM_SINGLETON

    with _TIMESFM_LOCK:
        if _TIMESFM_SINGLETON is None:
            from app.models.transformer_model import TimesFMModel
            logger.info("Loading TimesFM (shared across all assigned categories)...")
            _TIMESFM_SINGLETON = TimesFMModel()
            logger.info("TimesFM loaded.")

    return _TIMESFM_SINGLETON


def get_forecaster(category: str, granularity: str) -> Forecaster:
    """Returns the specific model assigned to a (category, granularity) pair.

    Falls back to SeasonalNaiveModel for any pair with no explicit
    assignment yet. Real models are lazily instantiated on first use and
    cached per (category, granularity) — except TimesFM, which is shared
    (see _get_timesfm_instance).
    """
    key = (category, granularity)

    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    with _MODEL_CACHE_LOCK:
        # Re-check after acquiring the lock — another thread may have
        # populated this key while we were waiting for it.
        if key in _MODEL_CACHE:
            return _MODEL_CACHE[key]

        model_id = _ASSIGNMENTS.get(key)


        if model_id == "timesfm":
            forecaster = _get_timesfm_instance()
        elif model_id == "lightgbm":
            from app.models.lightgbm_model import LightGBMForecaster
            forecaster = LightGBMForecaster(category=category, granularity=granularity)
        elif model_id == "theta":
            from app.models.theta_model import ThetaForecaster
            forecaster = ThetaForecaster()
        elif model_id == "xgboost":
            from app.models.xgboost_model import XGBoostForecaster
            forecaster = XGBoostForecaster(category=category)
        else:
            forecaster = _BASELINE

        _MODEL_CACHE[key] = forecaster
        return forecaster


def warm_up_models() -> None:
    """Eagerly loads every assigned model at startup instead of on first
    request. Reuses get_forecaster() itself so there's exactly one code
    path for "load a model" — warm-up and lazy-load can never drift apart.

    A missing artifact here is handled the same way it is in
    trends_service/compare.py: log and skip, don't let one bad category
    stop the rest of the app from starting.
    """
    logger.info(f"Warming up {len(_ASSIGNMENTS)} model assignments...")
    failures = []

    for category, granularity in _ASSIGNMENTS:
        try:
            get_forecaster(category, granularity)
        except Exception as e:
            logger.warning(f"Warm-up failed for {category}/{granularity}: {e}")
            failures.append((category, granularity))

    logger.info(f"Warm-up complete. {len(_ASSIGNMENTS) - len(failures)} loaded, {len(failures)} failed.")