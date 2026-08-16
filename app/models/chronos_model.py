import numpy as np
import torch
from chronos import BaseChronosPipeline

from app.models.base import Forecaster, ForecastResult


def _nearest_quantile_index(quantile_levels, target: float) -> int:
    """Find the index of the quantile level closest to `target`.

    BaseChronosPipeline returns a FIXED set of quantile levels (typically
    9: 0.1 ... 0.9 for the default Bolt checkpoint) — this is not a sample
    dimension, so calling .median()/.quantile() directly on that axis is
    mathematically wrong (that computes a "quantile of quantiles", not the
    actual median forecast). This looks up the real index for a given
    target quantile (0.1 / 0.5 / 0.9) instead of assuming a fixed position.
    """
    levels = np.asarray(quantile_levels, dtype=float)
    return int(np.argmin(np.abs(levels - target)))


class ChronosForecaster(Forecaster):
    name = "Chronos (Bolt)"

    def __init__(self, model_name: str = "amazon/chronos-bolt-small"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = BaseChronosPipeline.from_pretrained(
            model_name,
            device_map=device,
        )

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        # seasonal_period is accepted for interface consistency with every
        # other Forecaster implementation, but Chronos infers periodicity
        # from context itself and doesn't need it directly.
        context = torch.tensor(
            np.asarray(history, dtype=np.float32)
        ).unsqueeze(0)

        forecast = self.pipeline.predict(context, prediction_length=horizon)
        # Shape: [batch=1, num_quantiles, horizon]
        forecast = forecast[0].detach().float().cpu().numpy()

        quantile_levels = getattr(self.pipeline, "quantile_levels", None)
        if quantile_levels is not None and len(quantile_levels) == forecast.shape[0]:
            median_idx = _nearest_quantile_index(quantile_levels, 0.5)
            lower_idx = _nearest_quantile_index(quantile_levels, 0.1)
            upper_idx = _nearest_quantile_index(quantile_levels, 0.9)
        else:
            # Fallback if quantile_levels isn't exposed by the installed
            # chronos-forecasting version: assume the documented default
            # symmetric 9-level layout (0.1 ... 0.9).
            median_idx = forecast.shape[0] // 2
            lower_idx = 0
            upper_idx = forecast.shape[0] - 1

        return ForecastResult(
            values=forecast[median_idx].tolist(),
            lower=forecast[lower_idx].tolist(),
            upper=forecast[upper_idx].tolist(),
        )