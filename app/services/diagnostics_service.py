import numpy as np
from statsmodels.tsa.seasonal import STL
from app.data.loader import get_category_history
from app.core.config import settings


def compute_diagnostics(category: str, granularity: str) -> dict:
    """Computes seasonality strength and volatility directly from the
    category's history using STL decomposition — no precomputed file needed.

    Feature definitions follow Hyndman & Athanasopoulos (Forecasting:
    Principles and Practice), which is why the formulas look like a ratio
    of residual variance rather than something more ad hoc.
    """
    history = get_category_history(category, granularity)
    period = settings.SEASONAL_PERIODS.get(granularity, 12)

    # STL needs at least 2 full seasonal cycles to decompose meaningfully
    if len(history) < period * 2:
        return {
            "seasonal_strength": None,
            "trend_strength": None,
            "cv": None,
            "notes": f"Not enough history ({len(history)} points) for a {period}-period seasonal decomposition",
        }

    values = history.to_numpy()

    try:
        stl = STL(values, period=period, robust=True).fit()
    except ValueError as e:
        # Can happen on pathological series (all-zero, all-identical values, etc.)
        return {
            "seasonal_strength": None,
            "trend_strength": None,
            "cv": None,
            "notes": f"STL decomposition failed: {e}",
        }

    var_resid = np.var(stl.resid)
    seasonal_strength = max(0.0, 1 - var_resid / np.var(stl.seasonal + stl.resid))
    trend_strength = max(0.0, 1 - var_resid / np.var(stl.trend + stl.resid))

    mean_val = np.mean(values)
    cv = float(np.std(values) / mean_val) if mean_val != 0 else None

    return {
        "seasonal_strength": float(seasonal_strength),
        "trend_strength": float(trend_strength),
        "cv": cv,
        "notes": "Computed live via STL decomposition",
    }