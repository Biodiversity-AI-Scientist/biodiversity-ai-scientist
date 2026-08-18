import logging
from typing import Any

from sqlalchemy.orm import Session

from src.database import get_db
from src.llm.contracts import (
    InvestigationPlanLLMOutput,
    InvestigationPlanningInput,
    ProposedInvestigationStepLLM,
)
from src.llm.exceptions import GatewayNotConfiguredError, LLMGatewayError
from src.llm.gateway import LLMGateway
from src.models import ResearchPlan, ResearchProject, ResearchQuestion

from src.repositories.investigation_step import (
    InvestigationStepRepository,
    check_for_cycle,
)
from src.schemas.investigation_step import (
    InvestigationPlanGenerationResponse,
    InvestigationStepResponse,
    InvestigationStepStatus,
)
from src.services.scientific_context import ScientificContextService

logger = logging.getLogger(__name__)


def generate_fallback_heuristic_plan(
    question_text: str,
    project_title: str,
) -> InvestigationPlanLLMOutput:
    """
    Constructs a scientifically sound non-prescriptive default investigation plan
    if the external LLM Gateway is offline or in mock testing mode.
    """
    steps = [
        ProposedInvestigationStepLLM(
            step_key="S1",
            display_order=1,
            title="Assess data availability and metadata completeness",
            scientific_goal="Audit sample coverage, geographic/taxonomic metadata, and sampling sufficiency.",
            rationale="Before analytical modeling or testing, empirical coverage and potential sampling gaps must be quantified.",
            step_type="data_assessment",
            requires_capability=True,
            requires_experiment=False,
            required_operation="Audit specimen counts, locality metadata, and taxonomic verification status",
            expected_evidence="Summary tables of specimen availability and missingness",
            completion_criteria="All candidate records evaluated; metadata gaps quantified; eligible cohort defined.",
            prerequisite_keys=[],
        ),
        ProposedInvestigationStepLLM(
            step_key="S2",
            display_order=2,
            title="Establish appropriate quantitative representation",
            scientific_goal="Derive or extract standardized, reproducible scientific representations for eligible specimens.",
            rationale="An explicit representation is required to test morphological, phenotypic, or biological patterns objectively.",
            step_type="representation",
            requires_capability=True,
            requires_experiment=True,
            required_operation="Extract normalized phenotypic features or visual/morphological embeddings",
            expected_evidence="Derived representation matrix or normalized artifact features",
            completion_criteria="Feature vectors or coordinates successfully generated and quality-audited for all cohort members.",
            prerequisite_keys=["S1"],
        ),
        ProposedInvestigationStepLLM(
            step_key="S3",
            display_order=3,
            title="Evaluate biological association and test focal hypotheses",
            scientific_goal="Test the focal relationship or hypothesis using an appropriate inferential framework.",
            rationale="Direct statistical or comparative analysis is required to address the primary scientific question.",
            step_type="statistical_analysis",
            requires_capability=True,
            requires_experiment=True,
            required_operation="Perform hypothesis testing and effect size estimation",
            expected_evidence="Statistical test metrics, effect sizes, and significance values",
            completion_criteria="Hypothesis tested against null expectation; test diagnostics and uncertainty documented.",
            prerequisite_keys=["S2"],
        ),
        ProposedInvestigationStepLLM(
            step_key="S4",
            display_order=4,
            title="Assess confounders and evaluate robustness",
            scientific_goal="Evaluate whether sampling biases, provider effects, or environmental confounders explain the findings.",
            rationale="Robustness checks ensure that observed signals reflect genuine biological variation rather than artifacts.",
            step_type="robustness",
            requires_capability=True,
            requires_experiment=True,
            required_operation="Sensitivity and confounder stratification analysis",
            expected_evidence="Robustness metrics across alternative subsets or control groupings",
            completion_criteria="Key confounders evaluated; sensitivity to sampling and analytical choices quantified.",
            prerequisite_keys=["S3"],
        ),
        ProposedInvestigationStepLLM(
            step_key="S5",
            display_order=5,
            title="Synthesize evidence and formulate candidate conclusions",
            scientific_goal="Integrate all accumulated findings, evaluate remaining uncertainty, and determine next steps.",
            rationale="Scientific conclusions require systematic evidence integration across all completed steps.",
            step_type="evidence_synthesis",
            requires_capability=False,
            requires_experiment=False,
            required_operation="Evidence synthesis and claim formulation",
            expected_evidence="Evidence synthesis summary and candidate scientific claim",
            completion_criteria="Evidence synthesized against focal hypothesis; limitations and open questions documented.",
            prerequisite_keys=["S4"],
        ),
    ]

    return InvestigationPlanLLMOutput(
        summary_rationale=f"Systematic, reproducible multi-stage investigation workflow to answer: \"{question_text}\"",
        steps=steps,
        identified_uncertainties=[
            "Potential metadata incompleteness across historical museum collections",
            "Possible unmeasured confounding factors requiring sensitivity evaluation",
        ],
    )


class InvestigationPlanningService:
    @classmethod
    def generate_plan_for_question(
        cls,
        db: Session,
        dwh_db: Session | None,
        question_id: int,
        research_plan_id: int | None = None,
        user_guidance: str | None = None,
        focus_areas: list[str] | None = None,
    ) -> InvestigationPlanGenerationResponse:
        """
        Orchestrates the generation of an explicit, DAG-structured InvestigationPlan
        from an approved ResearchPlan and focal ResearchQuestion.
        """
        # 1. Enforce Question and Project
        question = db.get(ResearchQuestion, question_id)
        if not question:
            raise ValueError(f"ResearchQuestion {question_id} not found")

        project = db.get(ResearchProject, question.project_id)
        if not project:
            raise ValueError(f"Project {question.project_id} not found")

        # 2. Enforce Approved or Active ResearchPlan
        plan: ResearchPlan | None = None
        if research_plan_id is not None:
            plan = db.get(ResearchPlan, research_plan_id)
            if not plan or plan.project_id != project.id:
                raise ValueError(f"ResearchPlan {research_plan_id} not found for this project")
        else:
            # Find latest approved plan, or latest active plan
            plan = (
                db.query(ResearchPlan)
                .filter(ResearchPlan.project_id == project.id, ResearchPlan.status == "approved")
                .order_by(ResearchPlan.version.desc(), ResearchPlan.id.desc())
                .first()
            )
            if not plan:
                plan = (
                    db.query(ResearchPlan)
                    .filter(ResearchPlan.project_id == project.id)
                    .order_by(ResearchPlan.version.desc(), ResearchPlan.id.desc())
                    .first()
                )

        if not plan:
            raise ValueError(
                "An approved or active ResearchPlan is required to generate an Investigation Plan. "
                "Please create/approve a ResearchPlan before investigation planning."
            )

        # 3. Assemble Scientific Context (Phase 7)
        context = ScientificContextService.build_investigation_planning_context(
            db=db,
            dwh_db=dwh_db,
            question_id=question_id,
            research_plan_id=plan.id,
            activate_orchestrator=True,
        )
        rendered_context = ScientificContextService.format_investigation_planning_context_for_prompt(context)

        # 4. Invoke LLM Gateway
        input_contract = InvestigationPlanningInput(
            rendered_context=rendered_context,
            user_guidance=user_guidance,
            focus_areas=focus_areas or [],
        )

        llm_output: InvestigationPlanLLMOutput
        model_provenance: dict[str, Any] = {}

        try:
            gateway = LLMGateway()
            gateway_res = gateway.invoke(
                template_id="investigation_planning_v1",
                inputs={
                    "rendered_context": rendered_context,
                    "user_guidance": user_guidance,
                    "focus_areas": focus_areas or [],
                },
            )
            llm_output = InvestigationPlanLLMOutput.model_validate(gateway_res.output)
            model_provenance = gateway_res.metadata.model_dump()
        except (GatewayNotConfiguredError, LLMGatewayError, Exception) as e:
            logger.warning("LLM Gateway invocation failed or unconfigured for investigation planning: %s. Using fallback plan.", e)
            llm_output = generate_fallback_heuristic_plan(
                question_text=question.question,
                project_title=project.title,
            )
            model_provenance = {
                "provider": "heuristic_fallback",
                "reason": str(e),
            }


        # 5. Validate DAG Semantics
        steps = llm_output.steps
        if not steps:
            raise ValueError("No investigation steps were produced by the planning engine.")

        step_keys = [s.step_key for s in steps]
        if len(step_keys) != len(set(step_keys)):
            raise ValueError("Duplicate step_keys detected in proposed investigation plan.")

        edges: list[tuple[str, str]] = []
        for s in steps:
            for p_key in s.prerequisite_keys:
                if p_key not in step_keys:
                    raise ValueError(f"Step '{s.step_key}' declares unknown prerequisite '{p_key}'.")
                if p_key == s.step_key:
                    raise ValueError(f"Step '{s.step_key}' cannot depend on itself.")
                edges.append((p_key, s.step_key))

        if check_for_cycle(step_keys, edges):
            raise ValueError("Proposed investigation steps contain a circular dependency cycle.")

        # 6. Atomic Database Persistence Transaction
        context_summary_dict = {
            "project_id": project.id,
            "question_id": question.id,
            "research_plan_id": plan.id,
            "plan_version": plan.version,
            "missing_information": context.missing_information,
            "activated_intelligence_layers": context.metadata.activated_intelligence_layers,
            "context_latency_ms": context.metadata.latency_ms,
        }

        try:
            # 6a. Create Generation Batch
            gen = InvestigationStepRepository.create_generation(
                db=db,
                project_id=project.id,
                question_id=question.id,
                research_plan_id=plan.id,
                summary_rationale=llm_output.summary_rationale,
                identified_uncertainties=llm_output.identified_uncertainties,
                model_provenance=model_provenance,
                context_summary=context_summary_dict,
            )

            # 6b. Insert InvestigationStep rows
            key_to_step_id: dict[str, int] = {}
            for s in sorted(steps, key=lambda x: x.display_order):
                from src.schemas.investigation_step import InvestigationStepCreate

                create_data = InvestigationStepCreate(
                    title=s.title,
                    scientific_goal=s.scientific_goal,
                    rationale=s.rationale,
                    step_type=s.step_type,
                    requires_capability=s.requires_capability,
                    requires_experiment=s.requires_experiment,
                    required_operation=s.required_operation,
                    expected_evidence=s.expected_evidence,
                    completion_criteria=s.completion_criteria,
                    display_order=s.display_order,
                    status=InvestigationStepStatus.PROPOSED,
                    researcher_notes=None,
                    prerequisite_step_ids=[],
                )
                db_step = InvestigationStepRepository.create_step(
                    db=db,
                    project_id=project.id,
                    question_id=question.id,
                    data=create_data,
                    generation_id=gen.id,
                    research_plan_id=plan.id,
                )
                key_to_step_id[s.step_key] = db_step.id

            # 6c. Insert InvestigationStepDependency rows
            for s in steps:
                current_step_id = key_to_step_id[s.step_key]
                for p_key in s.prerequisite_keys:
                    prereq_step_id = key_to_step_id[p_key]
                    InvestigationStepRepository.add_dependency(
                        db=db,
                        step_id=current_step_id,
                        depends_on_step_id=prereq_step_id,
                    )

            # Commit the atomic transaction
            db.commit()

        except Exception as e:
            db.rollback()
            logger.exception("Failed to persist investigation plan atomically: %s", e)
            raise ValueError(f"Failed to persist investigation plan atomically: {e}")

        # 7. Format and Return Generation Response
        step_responses = InvestigationStepRepository.list_step_responses_for_question(
            db=db,
            question_id=question.id,
            generation_id=gen.id,
        )

        return InvestigationPlanGenerationResponse(
            id=gen.id,
            project_id=gen.project_id,
            question_id=gen.question_id,
            research_plan_id=gen.research_plan_id,
            summary_rationale=gen.summary_rationale,
            identified_uncertainties=gen.identified_uncertainties,
            model_provenance=gen.model_provenance,
            context_summary=gen.context_summary,
            created_at=gen.created_at,
            steps_count=len(step_responses),
            steps=step_responses,
        )
