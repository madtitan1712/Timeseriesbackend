from pydantic import BaseModel
from typing import Dict

class FreshnessResponse(BaseModel):
    last_dates: Dict[str, str]
    notes: Dict[str, str]