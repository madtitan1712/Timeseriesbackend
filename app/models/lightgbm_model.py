import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from app.models.base import Forecaster, ForecastResult
from app.data.loader import load_dataset
from app.core.config import settings


class LightGBMForecaster(Forecaster):
    name = "LightGBM"

    def __init__(self, category: str, granularity: str, models_dir: str = "models"):
        self.category = category
        self.granularity = granularity
        root_dir = Path(__file__).resolve().parent.parent.parent
        # Resolves to a "models" folder at the root of your project (next to "app")
        # Adjust this path if your .joblib files are stored elsewhere.
        self.models_dir = root_dir / models_dir

        path = self.models_dir / f"lgbm_{self.granularity}_{self.category}.joblib"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file {path} not found.")

        # Load once and keep in memory (the registry caches this instance)
        artifact = joblib.load(path)
        self.model = artifact['model']
        self.lags = artifact['lags']

    def _build_features(self, current_history: pd.Series, target_date: pd.Timestamp) -> pd.DataFrame:
        """Constructs the exact feature array LightGBM expects."""
        feat_dict = {}

        for l in self.lags:
            feat_dict[f'lag_{l}'] = current_history.iloc[-l]

        if self.granularity == 'daily':
            feat_dict['day_of_week'] = target_date.dayofweek
            feat_dict['month'] = target_date.month
            feat_dict['is_weekend'] = int(target_date.dayofweek in [5, 6])
        else:
            feat_dict['month'] = target_date.month
            feat_dict['week_of_year'] = target_date.isocalendar().week

        return pd.DataFrame([feat_dict])

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        """Generates a multi-step forecast matching the dashboard's interface."""

        # 1. Reconstruct the DatetimeIndex for the history
        # (Since the base interface only passes a flat numpy array)
        df = load_dataset(self.granularity)
        cat_df = df[['datum', self.category]].dropna().reset_index(drop=True)
        rolling_history = pd.Series(cat_df[self.category].values, index=cat_df['datum'])

        current_date = rolling_history.index[-1]
        step_delta = pd.Timedelta(days=1) if self.granularity == 'daily' else pd.Timedelta(weeks=1)

        predictions = []

        # 2. Iterative forecasting
        for _ in range(horizon):
            target_date = current_date + step_delta

            # Build features for this exact step
            X_next = self._build_features(rolling_history, target_date)

            # Ensure column order matches training exactly
            X_next = X_next[self.model.feature_name_]

            # Predict & clamp negatives to 0
            y_pred = max(0.0, float(self.model.predict(X_next)[0]))
            predictions.append(y_pred)

            # Append to history so the NEXT iteration can use it as a lag
            rolling_history.loc[target_date] = y_pred
            current_date = target_date

        # 3. Return the standard Pydantic response shape
        return ForecastResult(values=predictions)