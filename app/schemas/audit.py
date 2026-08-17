from pydantic import BaseModel
from typing import List, Optional

class ModelPerformanceRow(BaseModel):
    model_name: str
    mase: Optional[float] = None
    smape: Optional[float] = None
    runtime_ms: int
    categories_scored: int

class AuditResponse(BaseModel):
    metrics: List[ModelPerformanceRow]
    evaluated_at: Optional[str] = None
    skipped_count: int = 0