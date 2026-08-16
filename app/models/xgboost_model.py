import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from app.models.base import Forecaster, ForecastResult
from app.data.loader import load_dataset


class XGBoostForecaster(Forecaster):
    name = "XGBoost"

    def __init__(self, category: str, models_dir: str = "models"):
        self.category = category

        # Navigate from app/models/xgboost_model.py back to the project root
        root_dir = Path(__file__).resolve().parent.parent.parent
        self.models_dir = root_dir / models_dir

        # Strictly hardcoded to weekly format
        path = self.models_dir / f"xgb_weekly_{self.category}.joblib"

        if not path.exists():
            raise FileNotFoundError(f"Model file {path} not found.")

        artifact = joblib.load(path)
        self.model = artifact['model']
        self.lags = artifact['lags']

    def _build_features(self, current_history: pd.Series, target_date: pd.Timestamp) -> pd.DataFrame:
        """Constructs the weekly feature array XGBoost expects."""
        feat_dict = {}

        for l in self.lags:
            feat_dict[f'lag_{l}'] = current_history.iloc[-l]

        # Only weekly calendar features are needed
        feat_dict['month'] = target_date.month
        feat_dict['week_of_year'] = target_date.isocalendar().week

        return pd.DataFrame([feat_dict])

    def predict(self, history: np.ndarray, horizon: int, seasonal_period: int) -> ForecastResult:
        """Generates a multi-step forecast matching the dashboard's interface."""

        # Always pull from the weekly dataset
        df = load_dataset("weekly")
        cat_df = df[['datum', self.category]].dropna().reset_index(drop=True)
        rolling_history = pd.Series(cat_df[self.category].values, index=cat_df['datum'])

        current_date = rolling_history.index[-1]
        step_delta = pd.Timedelta(weeks=1)

        predictions = []

        for _ in range(horizon):
            target_date = current_date + step_delta

            # Build features for this exact step
            X_next = self._build_features(rolling_history, target_date)

            # Ensure column order matches training exactly
            if hasattr(self.model, 'feature_names_in_'):
                X_next = X_next[self.model.feature_names_in_]

            # Predict & clamp negatives to 0
            y_pred = max(0.0, float(self.model.predict(X_next)[0]))
            predictions.append(y_pred)

            # Append to history so the NEXT iteration can use it as a lag
            rolling_history.loc[target_date] = y_pred
            current_date = target_date

        return ForecastResult(values=predictions)