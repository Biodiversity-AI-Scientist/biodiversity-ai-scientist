from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.scientific_capability import ScientificCapabilityResponse


class ScientificContextType(str, Enum):
    BRAINSTORMING = "brainstorming"
    INVESTIGATION_PLANNING = "investigation_planning"
    CAPABILITY_MATCHING = "capability_matching"
    EXPERIMENT_PLANNING = "experiment_planning"
    RESULT_INTERPRETATION = "result_interpretation"


class ContextProvenanceRecord(BaseModel):
    source_type: str = Field(description="e.g. DATABASE_WORLD_MODEL, DWH_SQL, WORMS_REST, RESEARCH_PROGRAM_STATE")
    entity_type: str = Field(description="e.g. ResearchQuestion, ResearchPlan, Hypothesis, DatasetVersion, Result")
    record_id: int | str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str | None = None



class ContextBuildMetadata(BaseModel):
    context_type: ScientificContextType
    latency_ms: float
    entity_counts: dict[str, int] = Field(default_factory=dict)
    missing_information: list[str] = Field(default_factory=list)
    activated_intelligence_layers: list[str] = Field(default_factory=list)
    rendered_char_count: int = 0


class ProjectContextSummary(BaseModel):
    id: int
    title: str
    description: str | None = None
    objective: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ResearchPlanContextSummary(BaseModel):
    id: int
    version: int
    title: str
    status: str
    objective: str | None = None
    scientific_background: str | list[str] | None = None
    primary_research_question: str | None = None
    secondary_research_questions: list[str] = Field(default_factory=list)
    candidate_hypotheses: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)
    available_data: str | list[str] | None = None
    additional_data_needed: str | list[str] | None = None
    proposed_strategy: str | list[str] | None = None
    analytical_stages: list[dict[str, Any]] = Field(default_factory=list)
    potential_confounders: list[str] = Field(default_factory=list)
    sources_of_bias: list[str] = Field(default_factory=list)
    validation_strategy: str | list[str] | None = None
    interpretation_criteria: str | list[str] | None = None
    limitations: list[str] = Field(default_factory=list)
    open_decisions: list[str] = Field(default_factory=list)
    recommended_next_step: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)



class ResearchQuestionContextSummary(BaseModel):
    id: int
    project_id: int
    text: str
    status: str | None = None
    inferential_level: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PredictionContextSummary(BaseModel):
    id: int
    hypothesis_id: int
    statement: str

    model_config = ConfigDict(from_attributes=True)


class HypothesisContextSummary(BaseModel):
    id: int
    question_id: int
    statement: str
    status: str | None = None
    rationale: str | None = None
    predictions: list[PredictionContextSummary] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class DatasetVersionContextSummary(BaseModel):
    id: int
    project_id: int
    version_key: str
    source_system: str
    member_count: int | None = None
    grouping_keys: list[Any] | None = None
    manifest_sha256: str | None = None
    selection_definition: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ResultContextSummary(BaseModel):
    id: int
    analysis_run_id: int
    analysis_plan_id: int | None = None
    result_type: str
    summary: str | None = None
    payload: dict[str, Any] | None = None
    uncertainty: dict[str, Any] | None = None
    diagnostics: dict[str, Any] | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ArtifactContextSummary(BaseModel):
    id: int
    project_id: int
    analysis_run_id: int | None = None
    artifact_type: str
    uri: str
    mime_type: str | None = None
    sha256: str
    size_bytes: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceContextSummary(BaseModel):
    id: int
    claim_id: int
    result_id: int | None = None
    artifact_id: int | None = None
    direction: str
    validity_status: str
    inferential_level: str | None = None
    summary: str | None = None
    limitations: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ClaimContextSummary(BaseModel):
    id: int
    question_id: int | None = None
    text: str
    claim_type: str
    epistemic_status: str
    scope: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DecisionContextSummary(BaseModel):
    id: int
    question_id: int | None = None
    decision_type: str
    outcome: str
    rationale: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReviewContextSummary(BaseModel):
    id: int
    claim_id: int | None = None
    analysis_run_id: int | None = None
    reviewer_role: str
    outcome: str
    comments: str | None = None
    findings: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


# ==============================================================================
# 1. Primary Deliverable: Investigation Planning Context
# ==============================================================================

class InvestigationPlanningContext(BaseModel):
    """
    Context assembled for the LLM to reason about:
    'What scientific steps are required to answer this ResearchQuestion?'
    """
    project: ProjectContextSummary
    research_plan: ResearchPlanContextSummary | None = None
    research_question: ResearchQuestionContextSummary
    hypotheses: list[HypothesisContextSummary] = Field(default_factory=list)
    available_datasets: list[DatasetVersionContextSummary] = Field(default_factory=list)
    available_artifacts: list[ArtifactContextSummary] = Field(default_factory=list)
    previous_results: list[ResultContextSummary] = Field(default_factory=list)
    existing_evidence: list[EvidenceContextSummary] = Field(default_factory=list)
    claims: list[ClaimContextSummary] = Field(default_factory=list)
    decisions: list[DecisionContextSummary] = Field(default_factory=list)
    reviews: list[ReviewContextSummary] = Field(default_factory=list)
    known_constraints: list[str] = Field(default_factory=list)
    known_biases: list[str] = Field(default_factory=list)
    unresolved_contradictions: list[str] = Field(default_factory=list)
    research_intelligence: dict[str, Any] | None = None
    missing_information: list[str] = Field(default_factory=list)
    provenance_records: list[ContextProvenanceRecord] = Field(default_factory=list)
    metadata: ContextBuildMetadata


# ==============================================================================
# 2. Future Context Contracts (Interfaces for later phases)
# ==============================================================================

class CapabilityMatchingContext(BaseModel):
    """
    Context assembled to answer: 'Which registered capability can perform this scientific step?'
    """
    project: ProjectContextSummary
    research_question: ResearchQuestionContextSummary
    investigation_step_goal: str
    required_input_types: list[str] = Field(default_factory=list)
    required_output_types: list[str] = Field(default_factory=list)
    available_datasets: list[DatasetVersionContextSummary] = Field(default_factory=list)
    candidate_capabilities: list[ScientificCapabilityResponse] = Field(default_factory=list)
    methodological_constraints: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    provenance_records: list[ContextProvenanceRecord] = Field(default_factory=list)
    metadata: ContextBuildMetadata


class ExperimentPlanningContext(BaseModel):
    """
    Context assembled to pre-specify a concrete Experiment (AnalysisPlan) from a capability.
    """
    project: ProjectContextSummary
    research_question: ResearchQuestionContextSummary
    hypothesis: HypothesisContextSummary | None = None
    selected_capability: ScientificCapabilityResponse | None = None
    intended_dataset: DatasetVersionContextSummary | None = None
    intended_artifacts: list[ArtifactContextSummary] = Field(default_factory=list)
    methodological_constraints: list[str] = Field(default_factory=list)
    parameter_schema: dict[str, Any] | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    previous_experiments: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    provenance_records: list[ContextProvenanceRecord] = Field(default_factory=list)
    metadata: ContextBuildMetadata


class ResultInterpretationContext(BaseModel):
    """
    Context assembled to evaluate: 'What does this real result mean for the ResearchQuestion?'
    """
    project: ProjectContextSummary
    research_question: ResearchQuestionContextSummary
    hypothesis: HypothesisContextSummary | None = None
    analysis_plan_id: int
    analysis_run_id: int
    run_status: str
    actual_parameters: dict[str, Any] | None = None
    dataset_version: DatasetVersionContextSummary | None = None
    results: list[ResultContextSummary] = Field(default_factory=list)
    artifacts: list[ArtifactContextSummary] = Field(default_factory=list)
    interpretation_criteria: str | None = None
    prior_evidence: list[EvidenceContextSummary] = Field(default_factory=list)
    claims: list[ClaimContextSummary] = Field(default_factory=list)
    reviews: list[ReviewContextSummary] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    provenance_records: list[ContextProvenanceRecord] = Field(default_factory=list)
    metadata: ContextBuildMetadata
