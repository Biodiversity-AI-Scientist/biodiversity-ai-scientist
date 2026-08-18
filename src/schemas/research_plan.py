from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchPlanContentSchema(BaseModel):
    working_title: str = Field(default="Research Plan")
    research_objective: str = Field(default="")
    scientific_background_or_rationale: str = Field(default="")
    primary_research_question: str = Field(default="")
    secondary_research_questions: list[str] = Field(default_factory=list)
    candidate_hypotheses: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)
    available_data: list[str] = Field(default_factory=list)
    additional_data_needed: list[str] = Field(default_factory=list)
    proposed_research_strategy: str = Field(default="")
    proposed_analytical_stages: list[str] = Field(default_factory=list)
    potential_confounders: list[str] = Field(default_factory=list)
    sources_of_bias: list[str] = Field(default_factory=list)
    validation_or_robustness_strategy: str = Field(default="")
    interpretation_criteria: str = Field(default="")
    possible_outcomes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    open_scientific_decisions: list[str] = Field(default_factory=list)
    recommended_next_step: str = Field(default="")

    model_config = ConfigDict(extra="ignore")


class ResearchPlanCreate(BaseModel):
    project_id: int = Field(ge=1)
    brainstorming_session_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=255)
    content: ResearchPlanContentSchema


class ResearchPlanUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=32)
    content: ResearchPlanContentSchema | None = None


class ResearchPlanRevise(BaseModel):
    steering_instructions: str = Field(min_length=1)


class ResearchPlanPromote(BaseModel):
    question_indices: list[int] = Field(default_factory=list)
    hypothesis_indices: list[int] = Field(default_factory=list)
    target_question_id: int | None = None


class ResearchPlanResponse(BaseModel):
    id: int
    project_id: int
    brainstorming_session_id: int | None
    parent_plan_id: int | None
    version: int
    title: str
    status: str
    content: dict[str, Any]
    model_provenance: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
