from pydantic import BaseModel
from typing import List

class ModelPerformanceRow(BaseModel):
    model_name: str
    mase: float
    smape: float
    runtime_ms: int

class AuditResponse(BaseModel):
    metrics: List[ModelPerformanceRow]