from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HypothesisCreate(BaseModel):
    statement: str = Field(min_length=1)
    rationale: str | None = None
    source: str | None = Field(default="user", max_length=32)
    brainstorming_session_id: int | None = Field(default=None, ge=1)


class HypothesisUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str | None = None
    rationale: str | None = None
    status: str | None = Field(default=None, max_length=32)



class HypothesisResponse(BaseModel):
    id: int
    question_id: int
    statement: str
    rationale: str | None
    status: str
    source: str | None
    brainstorming_session_id: int | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
