from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.recommendation_config import (
    DEFAULT_ASSUMPTIONS,
    RECOMMENDATION_THRESHOLDS,
    RECOMMENDATION_WEIGHTS,
    clamp,
)
from app.data.loader import get_categories, get_category_history, load_dataset
from app.services.forecast_service import generate_forecast
from app.services.freshness_service import get_freshness_data
from app.models.registry import get_forecaster


def _normalize_volatility(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"high", "elevated", "volatile"}:
            return "high"
        if normalized in {"medium", "moderate"}:
            return "medium"
        if normalized in {"low", "stable", "normal"}:
            return "low"
    return "medium"


def _normalize_seasonality(value: Any) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"high", "strong", "highly seasonal", "seasonal"}:
            return "high"
        if normalized in {"medium", "moderate"}:
            return "medium"
        if normalized in {"low", "weak", "low seasonality"}:
            return "low"
    return "medium"


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _compute_freshness_score(data_staleness_days: int) -> float:
    if data_staleness_days <= 0:
        return 1.0
    if data_staleness_days >= RECOMMENDATION_THRESHOLDS.stale_days_threshold:
        return 0.4
    return 1.0 - min(0.6, data_staleness_days / RECOMMENDATION_THRESHOLDS.stale_days_threshold * 0.6)


def compute_confidence(
    freshness_score: float,
    model_quality_score: float,
    forecast_consistency: float,
    volatility_penalty: float,
    missing_data_penalty: float,
) -> float:
    score = (
        RECOMMENDATION_WEIGHTS.freshness_weight * freshness_score
        + RECOMMENDATION_WEIGHTS.model_quality_weight * model_quality_score
        + RECOMMENDATION_WEIGHTS.forecast_consistency_weight * forecast_consistency
        - RECOMMENDATION_WEIGHTS.volatility_penalty_weight * volatility_penalty
        - RECOMMENDATION_WEIGHTS.missing_data_penalty_weight * missing_data_penalty
    )
    return clamp(score)


def _determine_priority(forecast_change_pct: float, data_staleness_days: int, anomaly_flag: bool) -> str:
    if anomaly_flag or data_staleness_days >= RECOMMENDATION_THRESHOLDS.stale_days_threshold:
        return "high"
    if forecast_change_pct >= RECOMMENDATION_THRESHOLDS.strong_growth_pct or forecast_change_pct <= RECOMMENDATION_THRESHOLDS.strong_decline_pct:
        return "high"
    if abs(forecast_change_pct) >= 8.0:
        return "medium"
    return "low"


def _make_action(forecast_change_pct: float, volatility_level: str, seasonality_strength: str, anomaly_flag: bool) -> str:
    if anomaly_flag:
        return "Escalate to pharmacist review before purchasing or replenishment."
    if forecast_change_pct > RECOMMENDATION_THRESHOLDS.strong_growth_pct:
        return "Increase reorder quantity and tighten replenishment cadence."
    if forecast_change_pct < RECOMMENDATION_THRESHOLDS.strong_decline_pct:
        return "Reduce stock exposure and delay non-critical replenishment."
    if volatility_level == "high":
        return "Use smaller, more frequent purchase cycles to reduce stock risk."
    if seasonality_strength == "high":
        return "Pre-build seasonal buffer inventory before the next demand spike."
    return "Maintain current stocking policy and monitor the next review window."


def _make_rationale(
    forecast_change_pct: float,
    volatility_level: str,
    seasonality_strength: str,
    anomaly_flag: bool,
    data_staleness_days: int,
) -> str:
    reasons = []
    if anomaly_flag:
        reasons.append("an anomaly was detected in recent activity")
    if forecast_change_pct > 0:
        reasons.append(f"forecast demand is up {forecast_change_pct:.1f}% over the next horizon")
    elif forecast_change_pct < 0:
        reasons.append(f"forecast demand is down {abs(forecast_change_pct):.1f}% over the next horizon")
    else:
        reasons.append("forecast trend remains near neutral")
    if volatility_level == "high":
        reasons.append("volatility is elevated, which raises replenishment risk")
    if seasonality_strength == "high":
        reasons.append("seasonality is strong and should be planned for in advance")
    if data_staleness_days >= RECOMMENDATION_THRESHOLDS.stale_days_threshold:
        reasons.append("data freshness is stale, so confidence should be reduced")
    return "; ".join(reasons) if reasons else "No material operating concern detected."


def build_category_recommendations(
    category: str,
    granularity: str,
    horizon: int,
    forecast_change_pct: float,
    volatility_level: str,
    seasonality_strength: str,
    anomaly_flag: bool,
    data_staleness_days: int,
    selected_model: str,
    model_quality_score: float,
    forecast_consistency: float,
) -> list[dict[str, Any]]:
    if not category:
        raise ValueError("Category is required for category-level recommendations.")

    forecast_change_pct = _coerce_float(forecast_change_pct, 0.0)
    volatility_level = _normalize_volatility(volatility_level)
    seasonality_strength = _normalize_seasonality(seasonality_strength)
    selected_model = selected_model or "Seasonal Naive"
    model_quality_score = clamp(_coerce_float(model_quality_score, 0.5), 0.0, 1.0)
    forecast_consistency = clamp(_coerce_float(forecast_consistency, 0.5), 0.0, 1.0)

    freshness_score = _compute_freshness_score(data_staleness_days)
    volatility_penalty = 0.5 if volatility_level == "high" else 0.2 if volatility_level == "medium" else 0.0
    missing_data_penalty = 0.0 if data_staleness_days <= 5 else 0.2
    confidence = compute_confidence(
        freshness_score=freshness_score,
        model_quality_score=model_quality_score,
        forecast_consistency=forecast_consistency,
        volatility_penalty=volatility_penalty,
        missing_data_penalty=missing_data_penalty,
    )

    priority = _determine_priority(forecast_change_pct, data_staleness_days, anomaly_flag)
    action = _make_action(forecast_change_pct, volatility_level, seasonality_strength, anomaly_flag)
    rationale = _make_rationale(forecast_change_pct, volatility_level, seasonality_strength, anomaly_flag, data_staleness_days)

    primary = {
        "recommendation_id": f"rec-cat-{category.lower()}-{granularity}-{horizon}-{int(datetime.now(timezone.utc).timestamp())}",
        "scope": "category",
        "category": category,
        "priority": priority,
        "action": action,
        "rationale": rationale,
        "evidence": {
            "forecast_change_pct": forecast_change_pct,
            "volatility_level": volatility_level,
            "seasonality_strength": seasonality_strength,
            "anomaly_flag": bool(anomaly_flag),
            "data_staleness_days": int(data_staleness_days),
            "selected_model": selected_model,
            "model_quality_score": model_quality_score,
        },
        "confidence_score": round(confidence, 4),
        "assumptions": list(DEFAULT_ASSUMPTIONS),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    secondary = []
    if volatility_level == "high":
        secondary.append(
            {
                "recommendation_id": f"rec-cat-{category.lower()}-{granularity}-safety-{int(datetime.now(timezone.utc).timestamp())}",
                "scope": "category",
                "category": category,
                "priority": "medium",
                "action": "Reduce order batch size and increase review frequency.",
                "rationale": "High volatility suggests demand swings are likely to create stock imbalance.",
                "evidence": {
                    "forecast_change_pct": forecast_change_pct,
                    "volatility_level": volatility_level,
                    "seasonality_strength": seasonality_strength,
                    "anomaly_flag": bool(anomaly_flag),
                    "data_staleness_days": int(data_staleness_days),
                    "selected_model": selected_model,
                    "model_quality_score": model_quality_score,
                },
                "confidence_score": round(max(0.35, confidence - 0.1), 4),
                "assumptions": list(DEFAULT_ASSUMPTIONS),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return [primary] + secondary


def build_portfolio_recommendations(
    granularity: str,
    category_summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recommendations = []
    for item in category_summaries or []:
        category = str(item.get("category") or "PORTFOLIO")
        forecast_change_pct = _coerce_float(item.get("forecast_change_pct"), 0.0)
        volatility_level = _normalize_volatility(item.get("volatility_level"))
        seasonality_strength = _normalize_seasonality(item.get("seasonality_strength"))
        anomaly_flag = bool(item.get("anomaly_flag"))
        data_staleness_days = int(_coerce_float(item.get("data_staleness_days"), 0))
        selected_model = str(item.get("selected_model") or "Seasonal Naive")
        model_quality_score = clamp(_coerce_float(item.get("model_quality_score"), 0.5), 0.0, 1.0)
        forecast_consistency = clamp(_coerce_float(item.get("forecast_consistency"), 0.5), 0.0, 1.0)

        category_recs = build_category_recommendations(
            category=category,
            granularity=granularity,
            horizon=12,
            forecast_change_pct=forecast_change_pct,
            volatility_level=volatility_level,
            seasonality_strength=seasonality_strength,
            anomaly_flag=anomaly_flag,
            data_staleness_days=data_staleness_days,
            selected_model=selected_model,
            model_quality_score=model_quality_score,
            forecast_consistency=forecast_consistency,
        )
        recommendations.extend(category_recs)

    recommendations.sort(
        key=lambda rec: (
            {"high": 0, "medium": 1, "low": 2}[rec["priority"]],
            -float(rec["confidence_score"]),
            str(rec["category"] or ""),
        )
    )
    return recommendations


def _summarize_category(category: str, granularity: str) -> dict[str, Any]:
    history = get_category_history(category, granularity)
    if history.empty:
        return {}

    forecast_res = generate_forecast(category, granularity, horizon=12)
    latest_actual = float(history.iloc[-1]) if len(history) else 0.0
    next_forecast = float(forecast_res.values[0]) if forecast_res.values else 0.0
    forecast_change_pct = ((next_forecast - latest_actual) / latest_actual * 100) if latest_actual > 0 else 0.0

    freshness_data = get_freshness_data()
    last_date = freshness_data.last_dates.get(granularity)
    data_staleness_days = 0
    if last_date and last_date != "N/A":
        last_dt = datetime.strptime(last_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        data_staleness_days = max(0, (datetime.now(timezone.utc) - last_dt).days)

    volatility_level = "medium"
    seasonality_strength = "medium"
    anomaly_flag = False

    forecaster = get_forecaster(category, granularity)
    selected_model = getattr(forecaster, "name", "Seasonal Naive")

    model_quality_score = 0.8
    forecast_consistency = 0.8

    return {
        "category": category,
        "forecast_change_pct": forecast_change_pct,
        "volatility_level": volatility_level,
        "seasonality_strength": seasonality_strength,
        "anomaly_flag": anomaly_flag,
        "data_staleness_days": data_staleness_days,
        "selected_model": selected_model,
        "model_quality_score": model_quality_score,
        "forecast_consistency": forecast_consistency,
        "latest_actual": latest_actual,
        "next_forecast": next_forecast,
    }


def get_portfolio_recommendations(granularity: str = "monthly") -> list[dict[str, Any]]:
    categories = get_categories(granularity)
    summaries = []
    for category in categories:
        summary = _summarize_category(category, granularity)
        if summary:
            summaries.append(summary)
    return build_portfolio_recommendations(granularity=granularity, category_summaries=summaries)


def get_category_recommendations(category: str, granularity: str = "monthly", horizon: int = 12) -> list[dict[str, Any]]:
    if not category:
        raise ValueError("Category is required.")

    summary = _summarize_category(category, granularity)
    if not summary:
        raise ValueError(f"Category '{category}' not found for granularity '{granularity}'.")

    summary["forecast_change_pct"] = _coerce_float(summary.get("forecast_change_pct"), 0.0)
    return build_category_recommendations(
        category=category,
        granularity=granularity,
        horizon=horizon,
        forecast_change_pct=summary["forecast_change_pct"],
        volatility_level=summary.get("volatility_level", "medium"),
        seasonality_strength=summary.get("seasonality_strength", "medium"),
        anomaly_flag=bool(summary.get("anomaly_flag", False)),
        data_staleness_days=int(_coerce_float(summary.get("data_staleness_days"), 0)),
        selected_model=str(summary.get("selected_model") or "Seasonal Naive"),
        model_quality_score=_coerce_float(summary.get("model_quality_score"), 0.8),
        forecast_consistency=_coerce_float(summary.get("forecast_consistency"), 0.8),
    )
