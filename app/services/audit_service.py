import json
import os
from collections import defaultdict
from app.core.config import settings


def get_model_audit() -> dict:
    path = os.path.join(settings.DATA_DIR, "model_performance.json")

    if not os.path.exists(path):
        return {"metrics": [], "evaluated_at": None, "notes": "No backtest has been run yet. Run scripts/run_backtest.py."}

    with open(path) as f:
        data = json.load(f)

    by_model = defaultdict(list)
    for row in data["results"]:
        by_model[row["model_name"]].append(row)

    metrics = []
    for model_name, rows in by_model.items():
        mase_vals = [r["mase"] for r in rows if r["mase"] is not None]
        smape_vals = [r["smape"] for r in rows if r["smape"] is not None]
        runtime_vals = [r["runtime_ms"] for r in rows]

        metrics.append({
            "model_name": model_name,
            "mase": round(sum(mase_vals) / len(mase_vals), 3) if mase_vals else None,
            "smape": round(sum(smape_vals) / len(smape_vals), 2) if smape_vals else None,
            "runtime_ms": round(sum(runtime_vals) / len(runtime_vals)) if runtime_vals else 0,
            "categories_scored": len(rows),
        })

    return {
        "metrics": metrics,
        "evaluated_at": data["evaluated_at"],
        "skipped_count": len(data.get("skipped", [])),
    }