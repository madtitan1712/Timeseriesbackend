import numpy as np
from app.models.base import Forecaster, ForecastResult
import timesfm


class TimesFMModel(Forecaster):
    name = "TimesFM"

    def __init__(self, context_len: int = 1024, horizon_len: int = 365):
        # Initialize using the TimesFM 2.5 PyTorch API
        self.tfm = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
            "google/timesfm-2.5-200m-pytorch"
        )

        # Compile the model with the specified forecast configuration
        self.tfm.compile(
            timesfm.ForecastConfig(
                max_context=context_len,
                max_horizon=horizon_len,
                normalize_inputs=True,
                infer_is_positive=True,
            )
        )

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        # Pass BOTH horizon and inputs explicitly using keyword arguments
        forecast, _ = self.tfm.forecast(
            horizon=horizon,
            inputs=[list(history)]
        )

        # The forecast is already sliced to the requested horizon by the model
        point_forecast = forecast[0].tolist()

        return ForecastResult(values=point_forecast)