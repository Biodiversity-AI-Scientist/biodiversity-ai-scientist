from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResearchProjectCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    objective: str | None = None


class ResearchProjectUpdate(BaseModel):
    title: str | None = None
    objective: str | None = None
    status: str | None = None


class ResearchProjectResponse(BaseModel):
    id: int
    title: str
    objective: str | None
    status: str
    archived_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


