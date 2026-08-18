from typing import Any, Callable
from pydantic import BaseModel
from src.llm.contracts import (
    BrainstormingTurnInput,
    BrainstormingTurnOutput,
    CapabilitySelectionLLMInput,
    CapabilitySelectionLLMOutput,
    EvidenceSummaryInput,
    EvidenceSummaryOutput,
    ExperimentPlanningLLMInput,
    ExperimentPlanningLLMOutput,
    InvestigationPlanLLMOutput,
    InvestigationPlanningInput,
    ResearchPlanGenerationInput,
    ResearchPlanGenerationOutput,
)

from src.llm.exceptions import GatewayRequestValidationError


class PromptTemplate:
    def __init__(
        self,
        template_id: str,
        input_model: type[BaseModel],
        output_model: type[BaseModel],
        instructions: str,
        render_func: Callable[[BaseModel], str] | None = None,
    ) -> None:
        self.template_id = template_id
        self.input_model = input_model
        self.output_model = output_model
        self.instructions = instructions
        self.render_func = render_func

    def render(self, value: BaseModel) -> str:
        if self.render_func is not None:
            return self.render_func(value)
        data = value.model_dump()
        notes = "\n".join(f"- {note}" for note in data.get("evidence_notes", []))
        return f"Research question:\n{data.get('research_question', '')}\n\nEvidence notes:\n{notes}"


def render_brainstorming_turn(value: BaseModel) -> str:
    data = value.model_dump()
    parts = []
    if data.get("project_title"):
        parts.append(f"Research Project: {data['project_title']}")
    if data.get("project_description"):
        parts.append(f"Project Description/Objective: {data['project_description']}")
    if data.get("existing_questions"):
        q_list = "\n".join(f"- {q}" for q in data["existing_questions"])
        parts.append(f"Existing Canonical Research Questions:\n{q_list}")
    if data.get("existing_hypotheses"):
        h_list = "\n".join(f"- {h}" for h in data["existing_hypotheses"])
        parts.append(f"Existing Canonical Hypotheses:\n{h_list}")
    if data.get("data_intelligence_context"):
        parts.append(
            f"=== GROUND TRUTH DATA INTELLIGENCE & MODEL REGISTRY (FROM LOCAL DWH) ===\n"
            f"{data['data_intelligence_context']}\n"
            f"========================================================================="
        )
    parts.append(f"Initial Research Idea:\n{data.get('initial_idea', '')}")
    history = "\n".join(data.get("conversation_history", []))
    parts.append(f"Conversation turns:\n{history}")
    return "\n\n".join(parts)


def render_research_plan_generation(value: BaseModel) -> str:
    data = value.model_dump()
    parts = [
        f"Research Project:\n{data.get('project_title', '')}",
        f"Initial Research Idea:\n{data.get('initial_idea', '')}",
    ]
    if data.get("accepted_questions"):
        q_list = "\n".join(f"- {q}" for q in data["accepted_questions"])
        parts.append(f"=== CANONICAL ACCEPTED RESEARCH QUESTIONS (PRIMARY PROJECT OBJECTIVES) ===\n{q_list}")
    if data.get("accepted_hypotheses"):
        h_list = "\n".join(f"- {h}" for h in data["accepted_hypotheses"])
        parts.append(f"=== CANONICAL ACCEPTED HYPOTHESES (TO BE TESTED IN PLAN) ===\n{h_list}")
    if data.get("data_intelligence_context"):
        parts.append(
            f"=== GROUND TRUTH DATA INTELLIGENCE & MODEL REGISTRY (FROM LOCAL DWH) ===\n"
            f"{data['data_intelligence_context']}\n"
            f"========================================================================="
        )
    parts.append(f"Conversation Context & Discussion:\n{data.get('conversation_summary', '')}")
    if data.get("steering_instructions"):
        parts.append(f"Steering Instructions:\n{data.get('steering_instructions', '')}")
    return "\n\n".join(parts)


def render_investigation_planning(value: BaseModel) -> str:
    data = value.model_dump()
    parts = [data.get("rendered_context", "")]
    if data.get("user_guidance"):
        parts.append(f"=== RESEARCHER GUIDANCE & PREFERENCES ===\n{data['user_guidance']}")
    if data.get("focus_areas"):
        focus_str = "\n".join(f"- {f}" for f in data["focus_areas"])
        parts.append(f"=== SPECIFIC FOCUS AREAS ===\n{focus_str}")
    return "\n\n".join(p for p in parts if p)


def render_capability_selection(value: BaseModel) -> str:
    data = value.model_dump()
    parts = [data.get("rendered_context", "")]
    parts.append(f"=== INVESTIGATION STEP SCIENTIFIC GOAL ===\n{data.get('step_goal', '')}")
    if data.get("required_operation"):
        parts.append(f"=== REQUIRED OPERATION ===\n{data['required_operation']}")
    if data.get("user_guidance"):
        parts.append(f"=== RESEARCHER GUIDANCE ===\n{data['user_guidance']}")
    return "\n\n".join(p for p in parts if p)


def render_experiment_planning(value: BaseModel) -> str:
    data = value.model_dump()
    parts = [data.get("rendered_context", "")]
    parts.append(f"=== INVESTIGATION STEP GOAL ===\n{data.get('step_goal', '')}")
    parts.append(f"=== SELECTED SCIENTIFIC CAPABILITY ===\n{data.get('capability_name', '')}")
    if data.get("user_guidance"):
        parts.append(f"=== RESEARCHER GUIDANCE & CONSTRAINTS ===\n{data['user_guidance']}")
    return "\n\n".join(p for p in parts if p)


TEMPLATES = {
    "evidence_summary_v1": PromptTemplate(
        template_id="evidence_summary_v1",
        input_model=EvidenceSummaryInput,
        output_model=EvidenceSummaryOutput,
        instructions="Summarize only the supplied biodiversity evidence. Separate limitations and report confidence from 0 to 1. Do not invent facts.",
    ),
    "brainstorming_turn_v1": PromptTemplate(
        template_id="brainstorming_turn_v1",
        input_model=BrainstormingTurnInput,
        output_model=BrainstormingTurnOutput,
        instructions=(
            "You are the Biodiversity AI Scientist operating under Grounded Cumulative Science principles. Provide a concise, rigorous scientific response assisting the researcher in exploring biodiversity, taxonomy, biosystematics, or morphological variation. "
            "Provide 1-3 suggested research questions and 1-3 testable candidate hypotheses. "
            "TRI-GROUNDED PRIORITIZATION: When evaluating, comparing, or recommending candidate taxa or projects, synthesize three distinct grounded dimensions: "
            "1. Data Feasibility: Ground recommendations in supplied DWH material metrics (verified image counts, species richness, usable classes >= 15 images). "
            "2. Research Program Value: Explicitly explain how studying the candidate taxon tests, extends, or replicates an unresolved question from prior lab research (e.g. cross-genus difficulty, hierarchical routing, leakage partitioning, DINOv3 clustering) OR identify a justified novel research opportunity. "
            "3. Domain & Literature Relevance: Incorporate biological, conchological, and taxonomic intelligence from supplied WoRMS records and arXiv/bioRxiv literature (e.g., accepted nomenclature, synonymy history, cryptic species complexes, morphological overlap, and molecular vs conchological discordances). When two taxa have similar data feasibility, prioritize the taxon with richer biological/taxonomic importance (e.g. active species complexes or revision needs). "
            "SCIENTIFIC GUARDRAILS & PROVENANCE: "
            "- Retain identifiable source citations (WoRMS AphiaIDs, arXiv/bioRxiv preprints, or local paper collections) for all taxonomic or literature statements. "
            "- Conflicting scientific evidence (such as discordant morphological vs molecular classifications) MUST remain visible and explicit, never silently reconciled or smoothed over. "
            "- Ground truth exclusion: Strictly check DWH.ModelNetwork. Do NOT recommend taxa with existing neural models (such as Conus, Harpa, Nerita, Pecten, Strombus, Trivia, Turbo, Voluta) for a new classifier without explicitly stating that a model checkpoint already exists. "
            "NEVER fabricate specimen counts, publications, or statistical results."
        ),
        render_func=render_brainstorming_turn,
    ),
    "research_plan_generation_v1": PromptTemplate(
        template_id="research_plan_generation_v1",
        input_model=ResearchPlanGenerationInput,
        output_model=ResearchPlanGenerationOutput,
        instructions=(
            "You are the Biodiversity AI Scientist. Synthesize the scientific brainstorming discussion into a rigorous, structured 20-field Research Plan. "
            "Fill out all fields of the required JSON output schema logically. "
            "MANDATORY CANONICAL ALIGNMENT: If Canonical Accepted Research Questions or Hypotheses are provided, the Research Plan MUST be formulated directly and specifically around those accepted questions and hypotheses (e.g., if the accepted question and hypothesis focus on Nassarius, the entire plan's working_title, research_objective, primary_research_question, candidate_hypotheses, methodology, and data requirements must be specifically dedicated to Nassarius). Do NOT write a generic candidate-ranking comparison when specific questions have already been accepted for the project. "
            "TRI-GROUNDED SYNTHESIS: Connect the research objective and methodology to (1) measured DWH material availability, (2) unresolved research program agenda items, and (3) domain/taxonomic nuances (such as cryptic complexes, WoRMS nomenclature, and aperture/ribbing landmarking). "
            "GROUND TRUTH GUARDRAIL: When Data Intelligence metrics from the local Data Warehouse are provided, incorporate the measured material availability directly into available_data, additional_data_needed, and potential_confounders. Do NOT fabricate publications, empirical measurements, or statistical p-values."
        ),
        render_func=render_research_plan_generation,
    ),
    "investigation_planning_v1": PromptTemplate(
        template_id="investigation_planning_v1",
        input_model=InvestigationPlanningInput,
        output_model=InvestigationPlanLLMOutput,
        instructions=(
            "You are the Biodiversity AI Scientist operating under Grounded Cumulative Science principles. "
            "Your task is to decompose the focal ResearchQuestion and approved ResearchPlan into an explicit, scientifically justified Directed Acyclic Graph (DAG) of InvestigationSteps. "
            "NON-PRESCRIPTIVE SCIENTIFIC WORKFLOW: Determine the scientifically necessary steps from the ResearchQuestion, ResearchPlan, available evidence, and constraints. "
            "Do NOT impose a predefined analytical sequence or arbitrary algorithmic recipe (such as hardcoded DINOv3 or PERMANOVA). "
            "Depending on the biological question, steps may involve taxonomy verification, literature review, sampling audit, molecular sequence acquisition, alignment, phylogenetic inference, morphological representation, classifier training, error analysis, statistical testing, sensitivity analysis, or evidence synthesis. "
            "STEP CONTRACT: For each step, provide: "
            "1. step_key: Temporary unique identifier (e.g. S1, S2, S3). "
            "2. title & scientific_goal: Concise description of the scientific milestone. "
            "3. rationale: Why this step is necessary to answer the ResearchQuestion. "
            "4. step_type: Extensible category (e.g. data_assessment, taxonomy, representation, statistical_analysis, robustness, evidence_synthesis). "
            "5. requires_capability: True if the step requires a registered external tool/API (e.g. WoRMS lookup, literature search, embedding extraction). "
            "6. requires_experiment: True if the step requires a defined evidence-generating computational or empirical procedure whose intended inputs and method are specified before execution and whose actual execution will be recorded as an Experiment Run. "
            "7. required_operation: High-level operation needed, independent of specific software implementations. "
            "8. expected_evidence: Expected empirical or analytical output. "
            "9. completion_criteria: Clear, unambiguous scientific criteria for when this step is legitimately complete. "
            "10. prerequisite_keys: List of step_keys that must be completed before this step can begin (must form a valid acyclic DAG). "
            "NEVER fabricate empirical results or assume missing data exists."
        ),
        render_func=render_investigation_planning,
    ),
    "capability_comparative_selection_v1": PromptTemplate(
        template_id="capability_comparative_selection_v1",
        input_model=CapabilitySelectionLLMInput,
        output_model=CapabilitySelectionLLMOutput,
        instructions=(
            "You are the Biodiversity AI Scientist operating under Grounded Cumulative Science principles. "
            "Your task is to evaluate the supplied candidate scientific capabilities and select the single best matched capability to execute the given InvestigationStep. "
            "SELECTION PRINCIPLES: "
            "1. Select the capability whose scientific purpose, input/output contracts, and reproducibility characteristics best fulfill the step's scientific goal and required operation. "
            "2. Provide an exhaustive scientific rationale explaining why the chosen tool is superior for this specific biological/empirical milestone. "
            "3. For EVERY candidate capability not selected, provide an explicit, non-trivial rejection reason. "
            "4. Note any known limitations (e.g. GPU hardware requirements, batch limits, potential conchological biases). "
            "5. Never invent or hallucinate capabilities not listed in the candidate registry."
        ),
        render_func=render_capability_selection,
    ),
    "experiment_planning_v1": PromptTemplate(
        template_id="experiment_planning_v1",
        input_model=ExperimentPlanningLLMInput,
        output_model=ExperimentPlanningLLMOutput,
        instructions=(
            "You are the Biodiversity AI Scientist operating under Grounded Cumulative Science principles (LLM Stage 4: Experiment Planning). "
            "Your task is to pre-specify a rigorous, concrete Experiment design for the target InvestigationStep and its selected scientific capability. "
            "EXPERIMENT DESIGN PRINCIPLES: "
            "1. Scientific Objective: Define a specific, testable hypothesis or empirical objective for this single experiment. "
            "2. Input Selection: Select the appropriate DatasetVersion ID and prior Artifact IDs from the supplied context. "
            "3. Protocol: Describe the exact, step-by-step analytical protocol to be executed. "
            "4. Parameter Pre-Specification: Specify concrete parameter key-value pairs strictly conforming to the capability's declared parameter schema. For every parameter, provide a clear scientific justification. "
            "5. Controls & Sensitivity: Define baseline controls, provider-adjusted subsets, or negative controls to prevent confounding. "
            "6. Replication & Seeds: Specify random seed numbers, cross-validation folds, or permutation iterations for strict reproducibility. "
            "7. Expected Outputs & Completion Criteria: List all metric names, figure types, or matrices produced, with unambiguous completion criteria. "
            "8. Interpretation Criteria: Define concrete numerical decision rules (e.g. significance thresholds, silhouette scores) for how empirical outcomes will be interpreted in downstream Phase 13. "
            "9. Confounders & Limitations: Explicitly state known biological or computational limitations. "
            "NEVER execute the experiment in this stage — this is strictly a pre-execution scientific specification stage."
        ),
        render_func=render_experiment_planning,
    ),
}






def get_template(template_id: str) -> PromptTemplate:
    try:
        return TEMPLATES[template_id]
    except KeyError as exc:
        raise GatewayRequestValidationError("Unknown prompt template") from exc
