from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvestigationStepStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    REJECTED = "rejected"


class ProposedInvestigationStepLLM(BaseModel):
    step_key: str = Field(description="Temporary stable identifier e.g. S1, S2")
    display_order: int = Field(default=1, description="Sequence index for display")
    title: str = Field(description="Concise, descriptive scientific title")
    scientific_goal: str = Field(description="What scientific milestone this step accomplishes")
    rationale: str = Field(description="Why this step is necessary to answer the ResearchQuestion")
    step_type: str = Field(description="Extensible category e.g. data_assessment, taxonomy, representation, statistical_analysis, robustness, evidence_synthesis")
    requires_capability: bool = Field(description="True if step uses an external API/tool/capability")
    requires_experiment: bool = Field(description="True if step defines an evidence-generating computational/empirical procedure recorded as an Experiment Run")
    required_operation: str | None = Field(default=None, description="Description of the operation needed, independent of specific software")
    expected_evidence: str | None = Field(default=None, description="Expected empirical or analytical output/evidence")
    completion_criteria: str = Field(description="Explicit criteria defining when this step is legitimately complete")
    prerequisite_keys: list[str] = Field(default_factory=list, description="List of step_keys that must complete before this step can begin")


class InvestigationPlanLLMOutput(BaseModel):
    summary_rationale: str = Field(description="Overall synthesis of how these steps systematically answer the ResearchQuestion")
    steps: list[ProposedInvestigationStepLLM] = Field(description="List of proposed investigation steps forming an acyclic DAG")
    identified_uncertainties: list[str] = Field(default_factory=list, description="Methodological risks, data gaps, or uncertainties identified during planning")


class InvestigationPlanGenerateRequest(BaseModel):
    research_plan_id: int | None = Field(default=None, description="Optional specific ResearchPlan ID (defaults to latest approved plan)")
    user_guidance: str | None = Field(default=None, description="Optional researcher guidance or methodological preferences")
    focus_areas: list[str] | None = Field(default=None, description="Optional biological or analytical aspects to emphasize")


class InvestigationStepCreate(BaseModel):
    title: str
    scientific_goal: str
    rationale: str
    step_type: str
    requires_capability: bool = False
    requires_experiment: bool = False
    required_operation: str | None = None
    expected_evidence: str | None = None
    completion_criteria: str | None = None
    display_order: int = 1
    status: InvestigationStepStatus = InvestigationStepStatus.PROPOSED
    researcher_notes: str | None = None
    prerequisite_step_ids: list[int] = Field(default_factory=list)


class InvestigationStepUpdate(BaseModel):
    title: str | None = None
    scientific_goal: str | None = None
    rationale: str | None = None
    step_type: str | None = None
    requires_capability: bool | None = None
    requires_experiment: bool | None = None
    required_operation: str | None = None
    expected_evidence: str | None = None
    completion_criteria: str | None = None
    display_order: int | None = None
    status: InvestigationStepStatus | None = None
    researcher_notes: str | None = None


class InvestigationStepResponse(BaseModel):
    id: int
    project_id: int
    question_id: int
    research_plan_id: int | None = None
    generation_id: int | None = None
    title: str
    scientific_goal: str
    rationale: str
    step_type: str
    requires_capability: bool
    requires_experiment: bool
    required_operation: str | None = None
    expected_evidence: str | None = None
    completion_criteria: str | None = None
    display_order: int
    status: str
    is_blocked: bool = False
    readiness_state: str = "ready"
    capability_selection_id: int | None = None
    selected_capability_id: int | None = None
    selected_capability_key: str | None = None
    selected_capability_display_name: str | None = None
    has_capability_gap: bool = False
    prerequisite_step_ids: list[int] = Field(default_factory=list)
    dependent_step_ids: list[int] = Field(default_factory=list)
    researcher_notes: str | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationPlanGenerationResponse(BaseModel):
    id: int
    project_id: int
    question_id: int
    research_plan_id: int | None = None
    summary_rationale: str | None = None
    identified_uncertainties: list[Any] | None = None
    model_provenance: dict[str, Any] | None = None
    context_summary: dict[str, Any] | None = None
    created_at: datetime
    steps_count: int = 0
    steps: list[InvestigationStepResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InvestigationDAGNode(BaseModel):
    id: int
    title: str
    step_type: str
    status: str
    is_blocked: bool
    readiness_state: str = "ready"
    requires_capability: bool
    requires_experiment: bool
    selected_capability_key: str | None = None
    has_capability_gap: bool = False
    display_order: int



class InvestigationDAGEdge(BaseModel):
    from_step_id: int
    to_step_id: int


class InvestigationDAGResponse(BaseModel):
    question_id: int
    nodes: list[InvestigationDAGNode]
    edges: list[InvestigationDAGEdge]
    total_steps: int
    approved_steps: int
    completed_steps: int
    blocked_steps: int
