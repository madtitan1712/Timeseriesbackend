from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecommendationEvidence(BaseModel):
    forecast_change_pct: float
    volatility_level: str
    seasonality_strength: str
    anomaly_flag: bool
    data_staleness_days: int
    selected_model: str
    model_quality_score: float


class RecommendationItem(BaseModel):
    recommendation_id: str
    scope: str = Field(..., pattern="^(portfolio|category)$")
    category: Optional[str] = None
    priority: str = Field(..., pattern="^(high|medium|low)$")
    action: str
    rationale: str
    evidence: RecommendationEvidence
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)
    created_at: datetime


class RecommendationFeedback(BaseModel):
    recommendation_id: str
    accepted: bool
    comments: Optional[str] = None
