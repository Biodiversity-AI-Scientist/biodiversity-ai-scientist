from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResearchQuestionCreate(BaseModel):
    question: str = Field(
        min_length=1,
    )

    parent_question_id: int | None = None

    inferential_level: str | None = Field(
        default=None,
        max_length=64,
    )

    source: str | None = Field(
        default="user",
        max_length=32,
    )

    brainstorming_session_id: int | None = Field(
        default=None,
        ge=1,
    )


class ResearchQuestionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str | None = None
    inferential_level: str | None = None
    status: str | None = Field(default=None, max_length=32)



class ResearchQuestionResponse(BaseModel):
    id: int
    project_id: int
    parent_question_id: int | None
    question: str
    inferential_level: str | None
    status: str
    source: str | None
    brainstorming_session_id: int | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
