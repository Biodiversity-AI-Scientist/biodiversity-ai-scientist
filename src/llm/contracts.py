from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceSummaryInput(StrictModel):
    research_question: str = Field(min_length=1, max_length=4000)
    evidence_notes: list[str] = Field(min_length=1, max_length=100)

class EvidenceSummaryOutput(StrictModel):
    summary: str = Field(min_length=1)
    limitations: list[str]
    confidence: float = Field(ge=0, le=1)

class BrainstormingTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    timestamp: str | None = None
    sequence: int = Field(ge=1)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    model_provenance: dict[str, Any] | None = None

class SessionCandidate(BaseModel):
    candidate_id: str
    type: Literal["question", "hypothesis"]
    text: str = Field(min_length=1)
    status: Literal["proposed", "accepted", "edited_and_accepted", "rejected"] = "proposed"
    source_turn_sequence: int = Field(ge=1)
    edited_text: str | None = None
    promoted_entity_id: int | None = None

class BrainstormingTurnInput(StrictModel):
    project_title: str = Field(default="Research Project")
    project_description: str = Field(default="")
    existing_questions: list[str] = Field(default_factory=list)
    existing_hypotheses: list[str] = Field(default_factory=list)
    initial_idea: str = Field(min_length=1, max_length=4000)
    conversation_history: list[str] = Field(default_factory=list)
    data_intelligence_context: str | None = None

class BrainstormingTurnOutput(StrictModel):
    reply: str = Field(min_length=1)
    suggested_questions: list[str] = Field(default_factory=list)
    candidate_hypotheses: list[str] = Field(default_factory=list)


class ResearchPlanGenerationInput(BaseModel):
    project_title: str = Field(default="Research Project")
    initial_idea: str = Field(default="Exploratory scientific research idea")
    accepted_questions: list[str] = Field(default_factory=list)
    accepted_hypotheses: list[str] = Field(default_factory=list)
    conversation_summary: str = Field(default="")
    steering_instructions: str = Field(default="")
    data_intelligence_context: str | None = None



class ResearchPlanGenerationOutput(BaseModel):
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

    @field_validator(
        "secondary_research_questions",
        "candidate_hypotheses",
        "alternative_explanations",
        "evidence_required",
        "available_data",
        "additional_data_needed",
        "proposed_analytical_stages",
        "potential_confounders",
        "sources_of_bias",
        "possible_outcomes",
        "limitations",
        "open_scientific_decisions",
        mode="before",
    )
    @classmethod
    def ensure_list_of_strings(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        if isinstance(v, str):
            lines = [line.strip().lstrip("-*0123456789. ") for line in v.split("\n") if line.strip()]
            return lines if lines else [v.strip()]
        return [str(v)]

    @field_validator(
        "working_title",
        "research_objective",
        "scientific_background_or_rationale",
        "primary_research_question",
        "proposed_research_strategy",
        "validation_or_robustness_strategy",
        "interpretation_criteria",
        "recommended_next_step",
        mode="before",
    )
    @classmethod
    def ensure_string(cls, v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, list):
            return "\n".join(str(item).strip() for item in v if str(item).strip())
        return str(v).strip()


class InvestigationPlanningInput(BaseModel):
    rendered_context: str = Field(min_length=1, description="Complete Phase 7 Investigation Planning Context rendered for prompt")
    user_guidance: str | None = None
    focus_areas: list[str] = Field(default_factory=list)


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


class CapabilitySelectionLLMInput(BaseModel):
    rendered_context: str = Field(min_length=1, description="Complete Phase 7 Capability Matching Context rendered for prompt")
    step_goal: str = Field(min_length=1, description="Scientific goal of the investigation step")
    required_operation: str | None = None
    user_guidance: str | None = None


class RejectedAlternativeLLM(BaseModel):
    capability_key: str = Field(description="Key of the candidate capability not chosen")
    rejection_reason: str = Field(description="Scientific or operational reason why this tool was rejected or deemed inferior for this step")


class CapabilitySelectionLLMOutput(BaseModel):
    selected_capability_key: str = Field(description="Key of the single best matched capability")
    scientific_rationale: str = Field(description="Exhaustive scientific justification for choosing this capability for the step's goal")
    rejected_alternatives: list[RejectedAlternativeLLM] = Field(default_factory=list, description="Explicit reasons for rejecting candidate alternatives")
    known_limitations: str | None = Field(default=None, description="Known operational or scientific limitations of the chosen tool for this step")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score in tool selection match")


class ParameterPreSpecification(BaseModel):
    parameter_name: str = Field(description="Name of the parameter conforming to capability schema")
    value: Any = Field(description="Pre-specified value for the parameter")
    scientific_justification: str = Field(description="Scientific rationale for choosing this parameter value")


class ExperimentPlanningLLMInput(BaseModel):
    rendered_context: str = Field(min_length=1, description="Complete Phase 7 Experiment Planning Context rendered for prompt")
    step_goal: str = Field(min_length=1, description="Scientific goal of the investigation step")
    capability_name: str = Field(description="Name of the selected scientific capability")
    user_guidance: str | None = None


class ExperimentPlanningLLMOutput(BaseModel):
    working_title: str = Field(description="Clear, descriptive scientific title for the experiment")
    scientific_objective: str = Field(description="Specific testable objective of this experiment run")
    selected_dataset_version_id: int | None = Field(default=None, description="ID of the selected DatasetVersion to use as input, if applicable")
    selected_artifact_ids: list[int] = Field(default_factory=list, description="IDs of prior Artifacts to use as input, if applicable")
    protocol_description: str = Field(description="Detailed step-by-step scientific protocol for this experiment")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Concrete pre-specified parameters conforming to the capability input schema")
    parameter_justifications: list[ParameterPreSpecification] = Field(default_factory=list, description="Scientific justifications for individual parameters")
    control_strategy: str | None = Field(default=None, description="Negative controls, baseline comparisons, or provider-adjustment strategies")
    replication_strategy: str | None = Field(default=None, description="Random seed specifications, cross-validation folds, or permutation counts")
    expected_outputs: list[str] = Field(default_factory=list, description="Expected empirical metrics, figures, matrices, or model artifacts")
    completion_criteria: str = Field(description="Unambiguous criteria for when this experiment is considered scientifically complete")
    interpretation_criteria: str = Field(description="Decision thresholds specifying how observed empirical outcomes map to biological conclusions")
    known_limitations_and_confounders: list[str] = Field(default_factory=list, description="Potential confounding factors, data limitations, or scope constraints")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score in the scientific validity of the experiment design")



class ProviderRequest(StrictModel):

    model: str
    instructions: str
    input_text: str
    schema_name: str
    output_schema: dict[str, Any]
    max_output_tokens: int = Field(gt=0)

class ProviderResponse(StrictModel):
    request_id: str
    status: str
    output_text: str
    input_tokens: int | None = None
    output_tokens: int | None = None

class InvocationMetadata(StrictModel):
    invocation_id: str
    provider: str
    model: str
    template_id: str
    schema_id: str
    provider_request_id: str
    provider_status: str
    attempts: int
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    prompt_sha256: str
    response_sha256: str

class GatewayResult(StrictModel):
    output: dict[str, Any]
    metadata: InvocationMetadata
