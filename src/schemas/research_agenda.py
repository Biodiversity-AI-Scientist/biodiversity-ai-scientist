from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


AgendaType = Literal[
    "open_question",
    "methodological_issue",
    "cross_study_hypothesis",
    "replication_need",
    "limitation",
    "research_opportunity",
]

AgendaStatus = Literal[
    "open",
    "investigating",
    "partially_resolved",
    "resolved",
]


class ResearchAgendaItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    type: AgendaType = "open_question"
    status: AgendaStatus = "open"
    origin_project_id: int | None = None
    origin_research_plan_id: int | None = None
    origin_result_id: int | None = None
    source_reference: str | None = Field(default=None, max_length=255)
    current_evidence: str | None = None
    known_limitations: str | None = None
    follow_up_opportunities: str | None = None


class ResearchAgendaItemCreate(ResearchAgendaItemBase):
    pass


class ResearchAgendaItemUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    type: AgendaType | None = None
    status: AgendaStatus | None = None
    origin_project_id: int | None = None
    origin_research_plan_id: int | None = None
    origin_result_id: int | None = None
    source_reference: str | None = Field(default=None, max_length=255)
    current_evidence: str | None = None
    known_limitations: str | None = None
    follow_up_opportunities: str | None = None


class ResearchAgendaItemResponse(ResearchAgendaItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


ResearchAgendaItemSummary = ResearchAgendaItemResponse

