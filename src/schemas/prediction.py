from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PredictionCreate(BaseModel):
    statement: str = Field(min_length=1)


class PredictionResponse(BaseModel):
    id: int
    hypothesis_id: int
    statement: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
