from fastapi import APIRouter
from app.schemas.audit import AuditResponse
from app.services.audit_service import get_model_audit

router = APIRouter()

@router.get("/audit/model-performance", response_model=AuditResponse)
def get_audit():
    """Reads the last backtest run's results. Run scripts/run_backtest.py
    to refresh — this endpoint does not compute metrics on request."""
    return get_model_audit()