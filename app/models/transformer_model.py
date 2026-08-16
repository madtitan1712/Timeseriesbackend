import numpy as np
from app.models.base import Forecaster, ForecastResult
import timesfm


class TimesFMModel(Forecaster):
    name = "TimesFM"

    def __init__(self, context_len: int = 512, horizon_len: int = 12):
        self.tfm = timesfm.TimesFm(
            context_len=context_len,
            horizon_len=horizon_len,
            input_patch_len=32,
            output_patch_len=128,
            num_layers=20,
            model_dims=1280,
            backend="cpu"  # Swap to "gpu" if CUDA is configured
        )
        self.tfm.load_from_checkpoint(repo_id="google/timesfm-1.0-200m")

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        # TimesFM expects 1D arrays for single series forecasting
        forecast, _ = self.tfm.forecast(list(history), forecast_context_len=len(history))

        # Slicing to the exact requested horizon
        point_forecast = forecast[0][:horizon]

        return ForecastResult(values=point_forecast.tolist())