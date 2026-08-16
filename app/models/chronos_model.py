import numpy as np
import torch
from app.models.base import Forecaster, ForecastResult
from chronos import ChronosPipeline


class ChronosModel(Forecaster):
    name = "Chronos 2 (Bolt)"

    def __init__(self):
        # Updated to use Chronos 2 (Bolt)
        self.pipeline = ChronosPipeline.from_pretrained(
            "amazon/chronos-bolt-small",
            device_map="cuda",  # Swap to "cuda" if configured
            torch_dtype=torch.float32,  # Consider torch.bfloat16 if using a compatible GPU
        )

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        context = torch.tensor(history)

        # Chronos returns [num_series, num_samples, prediction_length]
        forecast_tensor = self.pipeline.predict(context, horizon)

        # Extract the median as the point forecast
        samples = forecast_tensor[0].numpy()
        median_forecast = np.median(samples, axis=0)

        # Calculate standard 80% prediction intervals
        lower = np.percentile(samples, 10, axis=0)
        upper = np.percentile(samples, 90, axis=0)

        return ForecastResult(
            values=median_forecast.tolist(),
            lower=lower.tolist(),
            upper=upper.tolist()
        )