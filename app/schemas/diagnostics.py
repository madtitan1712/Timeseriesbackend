from pydantic import BaseModel

class DiagnosticsResponse(BaseModel):
    category: str
    seasonality_strength: str
    volatility: str
    notes: str