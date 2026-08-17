import json
import time
from datetime import datetime, timezone
import numpy as np
from app.data.loader import get_category_history
from app.models.registry import get_forecaster, _ASSIGNMENTS
from app.core.config import settings


def mase(actual, forecast, train, period):
    diff_lag = period if len(train) > period else 1
    naive_errors = np.abs(np.diff(train, n=1)[::diff_lag]) if diff_lag > 1 else np.abs(np.diff(train))
    scale = np.mean(naive_errors) if len(naive_errors) else 0
    if scale == 0:
        return None
    return float(np.mean(np.abs(np.array(actual) - np.array(forecast))) / scale)


def smape(actual, forecast):
    actual, forecast = np.array(actual), np.array(forecast)
    denom = np.abs(actual) + np.abs(forecast)
    denom[denom == 0] = 1
    return float(100 * np.mean(2 * np.abs(actual - forecast) / denom))


def run():
    results = []
    skipped = []

    for (category, granularity), model_id in _ASSIGNMENTS.items():
        history = get_category_history(category, granularity)
        period = settings.SEASONAL_PERIODS[granularity]
        test_horizon = min(12, max(1, len(history) // 4))

        if len(history) < period * 2 + test_horizon:
            skipped.append({"category": category, "granularity": granularity, "reason": "insufficient history"})
            continue

        train, test = history[:-test_horizon], history[-test_horizon:]

        try:
            forecaster = get_forecaster(category, granularity)
            start = time.perf_counter()
            result = forecaster.predict(train.to_numpy(), horizon=test_horizon, seasonal_period=period)
            runtime_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            # Missing joblib, TimesFM load failure, etc. — skip this pair, don't kill the run
            skipped.append({"category": category, "granularity": granularity, "reason": str(e)})
            continue

        m = mase(test.tolist(), result.values, train.to_numpy(), period)
        s = smape(test.tolist(), result.values)

        results.append({
            "model_name": forecaster.name,
            "category": category,
            "granularity": granularity,
            "mase": m,
            "smape": s,
            "runtime_ms": round(runtime_ms, 1),
        })

    output = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "skipped": skipped,
    }

    out_path = f"{settings.DATA_DIR}/model_performance.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote {len(results)} results, skipped {len(skipped)}, to {out_path}")


if __name__ == "__main__":
    run()