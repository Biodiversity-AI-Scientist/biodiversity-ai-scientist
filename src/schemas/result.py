from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ResultResponse(BaseModel):
    id: int
    analysis_run_id: int
    result_type: str
    summary: str | None
    payload: dict[str, Any] | None
    uncertainty: dict[str, Any] | None
    diagnostics: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
