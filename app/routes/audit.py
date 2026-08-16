from fastapi import APIRouter
from app.schemas.audit import AuditResponse, ModelPerformanceRow

router = APIRouter()

@router.get("/audit/model-performance", response_model=AuditResponse)
def get_model_audit():
    """Reads the model-selection team's export file. Mocked for now."""
    return AuditResponse(
        metrics=[
            ModelPerformanceRow(model_name="Seasonal Naive", mase=1.0, smape=15.2, runtime_ms=5),
            ModelPerformanceRow(model_name="Chronos (Bolt)", mase=0.82, smape=12.1, runtime_ms=450),
            ModelPerformanceRow(model_name="TimesFM", mase=0.79, smape=11.5, runtime_ms=390),
            ModelPerformanceRow(model_name="LightGBM", mase=0.85, smape=13.0, runtime_ms=50),
        ]
    )