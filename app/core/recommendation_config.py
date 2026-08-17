from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecommendationWeights:
    freshness_weight: float = 0.30
    model_quality_weight: float = 0.30
    forecast_consistency_weight: float = 0.20
    volatility_penalty_weight: float = 0.10
    missing_data_penalty_weight: float = 0.10


@dataclass(frozen=True)
class RecommendationThresholds:
    strong_growth_pct: float = 15.0
    strong_decline_pct: float = -15.0
    high_volatility_score: float = 0.75
    strong_seasonality_score: float = 0.75
    stale_days_threshold: int = 7
    anomaly_confidence_penalty: float = 0.15
    low_confidence_floor: float = 0.35


RECOMMENDATION_WEIGHTS = RecommendationWeights()
RECOMMENDATION_THRESHOLDS = RecommendationThresholds()


DEFAULT_ASSUMPTIONS = [
    "Uses current forecast and freshness signals.",
    "Model quality and data freshness are included in the confidence score.",
    "No retraining occurs during request-time inference.",
]


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))
