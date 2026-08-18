import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from src.models.analysis_plan import AnalysisPlan
from src.models.analysis_run import AnalysisRun
from src.models.artifact import Artifact
from src.models.claim import Claim
from src.models.dataset_version import DatasetVersion
from src.models.decision import Decision
from src.models.evidence_item import EvidenceItem
from src.models.hypothesis import Hypothesis
from src.models.investigation_step import InvestigationStep
from src.models.prediction import Prediction
from src.models.research_plan import ResearchPlan
from src.models.research_project import ResearchProject
from src.models.research_question import ResearchQuestion
from src.models.result import Result
from src.models.review import Review
from src.models.scientific_capability import CapabilitySelection, ScientificApplication, ScientificCapability
from src.schemas.scientific_capability import ScientificCapabilityResponse
from src.schemas.scientific_context import (
    ArtifactContextSummary,
    CapabilityMatchingContext,
    ClaimContextSummary,
    ContextBuildMetadata,
    ContextProvenanceRecord,
    DatasetVersionContextSummary,
    DecisionContextSummary,
    EvidenceContextSummary,
    ExperimentPlanningContext,
    HypothesisContextSummary,
    InvestigationPlanningContext,
    PredictionContextSummary,
    ProjectContextSummary,
    ResearchPlanContextSummary,
    ResearchQuestionContextSummary,
    ResultContextSummary,
    ResultInterpretationContext,
    ReviewContextSummary,
    ScientificContextType,
)


class ScientificContextService:
    """
    Central Generalized Scientific Context Service.
    Assembles task-specific, provenance-aware scientific state for LLM reasoning
    without dumping the entire database or inventing missing facts.
    """

    # --------------------------------------------------------------------------
    # 1. Primary Deliverable: Investigation Planning Context
    # --------------------------------------------------------------------------
    @classmethod
    def build_investigation_planning_context(
        cls,
        db: Session,
        dwh_db: Session | None,
        question_id: int,
        research_plan_id: int | None = None,
        activate_orchestrator: bool = True,
    ) -> InvestigationPlanningContext:
        """
        Assembles structured scientific context to determine:
        'What scientific steps are required to answer this ResearchQuestion?'
        """
        start_time = time.time()
        provenance_records: list[ContextProvenanceRecord] = []
        missing_info: list[str] = []
        entity_counts: dict[str, int] = {}

        # 1. Focal Research Question
        question = db.get(ResearchQuestion, question_id)
        if not question:
            raise ValueError(f"ResearchQuestion with ID {question_id} not found")

        q_summary = ResearchQuestionContextSummary(
            id=question.id,
            project_id=question.project_id,
            text=question.question,
            status=question.status,
            inferential_level=question.inferential_level,
        )
        provenance_records.append(
            ContextProvenanceRecord(
                source_type="DATABASE_WORLD_MODEL",
                entity_type="ResearchQuestion",
                record_id=question.id,
                notes=f"Focal question: {question.question[:60]}...",
            )
        )
        entity_counts["research_question"] = 1

        # 2. Project Identity
        project = db.get(ResearchProject, question.project_id)
        if not project:
            raise ValueError(f"ResearchProject with ID {question.project_id} not found")

        project_summary = ProjectContextSummary(
            id=project.id,
            title=project.title,
            description=getattr(project, "description", None),
            objective=getattr(project, "objective", None),
        )
        provenance_records.append(
            ContextProvenanceRecord(
                source_type="DATABASE_WORLD_MODEL",
                entity_type="ResearchProject",
                record_id=project.id,
            )
        )
        entity_counts["project"] = 1

        # 3. Approved / Current ResearchPlan
        plan: ResearchPlan | None = None
        if research_plan_id is not None:
            plan = (
                db.query(ResearchPlan)
                .filter(
                    ResearchPlan.id == research_plan_id,
                    ResearchPlan.project_id == project.id,
                )
                .first()
            )
        else:
            # Prefer approved plan, otherwise latest version
            plan = (
                db.query(ResearchPlan)
                .filter(
                    ResearchPlan.project_id == project.id,
                    ResearchPlan.status == "approved",
                )
                .order_by(desc(ResearchPlan.version), desc(ResearchPlan.id))
                .first()
            )
            if not plan:
                plan = (
                    db.query(ResearchPlan)
                    .filter(ResearchPlan.project_id == project.id)
                    .order_by(desc(ResearchPlan.version), desc(ResearchPlan.id))
                    .first()
                )

        plan_summary: ResearchPlanContextSummary | None = None
        if plan:
            c = plan.content or {}
            plan_summary = ResearchPlanContextSummary(
                id=plan.id,
                version=plan.version,
                title=plan.title,
                status=plan.status,
                objective=c.get("research_objective") or c.get("objective") or project_summary.objective,
                scientific_background=c.get("scientific_background") or c.get("background"),
                primary_research_question=c.get("primary_research_question"),
                secondary_research_questions=c.get("secondary_research_questions") or [],
                candidate_hypotheses=c.get("candidate_hypotheses") or [],
                alternative_explanations=c.get("alternative_explanations") or [],
                evidence_required=c.get("evidence_required") or [],
                available_data=c.get("available_data"),
                additional_data_needed=c.get("additional_data_needed"),
                proposed_strategy=c.get("proposed_analytical_strategy") or c.get("proposed_strategy"),
                analytical_stages=c.get("analytical_stages") or [],
                potential_confounders=c.get("important_confounders") or c.get("potential_confounders") or [],
                sources_of_bias=c.get("sources_of_bias") or [],
                validation_strategy=c.get("validation_strategy"),
                interpretation_criteria=c.get("interpretation_criteria"),
                limitations=c.get("limitations") or [],
                open_decisions=c.get("open_decisions") or [],
                recommended_next_step=c.get("recommended_next_step"),
                created_at=plan.created_at,
            )
            provenance_records.append(
                ContextProvenanceRecord(
                    source_type="DATABASE_WORLD_MODEL",
                    entity_type="ResearchPlan",
                    record_id=plan.id,
                    notes=f"Plan v{plan.version} ({plan.status})",
                )
            )
            entity_counts["research_plan"] = 1
        else:
            missing_info.append("No ResearchPlan exists for this project.")
            entity_counts["research_plan"] = 0

        # 4. Related Hypotheses & Predictions (Focal Question Only)
        hypotheses_db = (
            db.query(Hypothesis)
            .filter(Hypothesis.question_id == question.id)
            .all()
        )
        hypotheses_summaries: list[HypothesisContextSummary] = []
        for h in hypotheses_db:
            preds = (
                db.query(Prediction)
                .filter(Prediction.hypothesis_id == h.id)
                .all()
            )
            pred_summaries = [
                PredictionContextSummary(
                    id=p.id,
                    hypothesis_id=p.hypothesis_id,
                    statement=p.statement,
                )
                for p in preds
            ]
            hypotheses_summaries.append(
                HypothesisContextSummary(
                    id=h.id,
                    question_id=h.question_id,
                    statement=h.statement,
                    status=h.status,
                    rationale=h.rationale,
                    predictions=pred_summaries,
                )
            )
            provenance_records.append(
                ContextProvenanceRecord(
                    source_type="DATABASE_WORLD_MODEL",
                    entity_type="Hypothesis",
                    record_id=h.id,
                )
            )
        entity_counts["hypotheses"] = len(hypotheses_summaries)
        if not hypotheses_summaries:
            missing_info.append("No candidate hypotheses currently linked to this ResearchQuestion.")

        # 5. Available Datasets & Artifacts
        datasets_db = (
            db.query(DatasetVersion)
            .filter(DatasetVersion.project_id == project.id)
            .all()
        )
        dataset_summaries = [
            DatasetVersionContextSummary(
                id=d.id,
                project_id=d.project_id,
                version_key=d.version_key,
                source_system=d.source_system,
                member_count=d.member_count,
                grouping_keys=d.grouping_keys,
                manifest_sha256=d.manifest_sha256,
                selection_definition=d.selection_definition,
            )
            for d in datasets_db
        ]
        entity_counts["datasets"] = len(dataset_summaries)
        if not dataset_summaries:
            missing_info.append("No frozen DatasetVersions registered for this project.")

        artifacts_db = (
            db.query(Artifact)
            .filter(Artifact.project_id == project.id)
            .limit(10)
            .all()
        )
        artifact_summaries = [
            ArtifactContextSummary(
                id=a.id,
                project_id=a.project_id,
                analysis_run_id=a.analysis_run_id,
                artifact_type=a.artifact_type,
                uri=a.uri,
                mime_type=a.mime_type,
                sha256=a.sha256,
                size_bytes=a.size_bytes,
            )
            for a in artifacts_db
        ]
        entity_counts["artifacts"] = len(artifact_summaries)

        # 6. Previous Results for this Question's Experiments (AnalysisPlans)
        plan_ids_stmt = select(AnalysisPlan.id).where(AnalysisPlan.question_id == question.id)
        plan_ids = list(db.scalars(plan_ids_stmt).all())
        run_ids: list[int] = []

        results_summaries: list[ResultContextSummary] = []
        if plan_ids:
            runs_stmt = select(AnalysisRun).where(
                AnalysisRun.analysis_plan_id.in_(plan_ids),
                AnalysisRun.status.in_(["completed", "failed"]),
            )
            runs = list(db.scalars(runs_stmt).all())
            run_ids = [r.id for r in runs]
            if run_ids:
                results_db = (
                    db.query(Result)
                    .filter(Result.analysis_run_id.in_(run_ids))
                    .all()
                )
                for res in results_db:
                    parent_run = next((r for r in runs if r.id == res.analysis_run_id), None)
                    results_summaries.append(
                        ResultContextSummary(
                            id=res.id,
                            analysis_run_id=res.analysis_run_id,
                            analysis_plan_id=parent_run.analysis_plan_id if parent_run else None,
                            result_type=res.result_type,
                            summary=res.summary,
                            payload=res.payload,
                            uncertainty=res.uncertainty,
                            diagnostics=res.diagnostics,
                            created_at=res.created_at,
                        )
                    )
                    provenance_records.append(
                        ContextProvenanceRecord(
                            source_type="DATABASE_WORLD_MODEL",
                            entity_type="Result",
                            record_id=res.id,
                            notes=f"From Experiment Run #{res.analysis_run_id}",
                        )
                    )

        entity_counts["previous_results"] = len(results_summaries)
        if not results_summaries:
            missing_info.append("No prior computational results produced for this question yet.")

        # 7. Claims, EvidenceItems, Decisions, Reviews
        claims_db = (
            db.query(Claim)
            .filter(
                (Claim.question_id == question.id)
                | ((Claim.project_id == project.id) & (Claim.question_id.is_(None)))
            )
            .all()
        )
        claim_summaries = [
            ClaimContextSummary(
                id=c.id,
                question_id=c.question_id,
                text=c.text,
                claim_type=c.claim_type,
                epistemic_status=c.epistemic_status,
                scope=c.scope,
            )
            for c in claims_db
        ]
        entity_counts["claims"] = len(claim_summaries)

        claim_ids = [c.id for c in claims_db]
        evidence_summaries: list[EvidenceContextSummary] = []
        if claim_ids:
            evidence_db = (
                db.query(EvidenceItem)
                .filter(EvidenceItem.claim_id.in_(claim_ids))
                .all()
            )
            for ev in evidence_db:
                evidence_summaries.append(
                    EvidenceContextSummary(
                        id=ev.id,
                        claim_id=ev.claim_id,
                        result_id=ev.result_id,
                        artifact_id=ev.artifact_id,
                        direction=ev.direction,
                        validity_status=ev.validity_status,
                        inferential_level=ev.inferential_level,
                        summary=ev.summary,
                        limitations=ev.limitations,
                    )
                )
        entity_counts["evidence_items"] = len(evidence_summaries)

        decisions_db = (
            db.query(Decision)
            .filter(
                (Decision.question_id == question.id)
                | ((Decision.project_id == project.id) & (Decision.question_id.is_(None)))
            )
            .all()
        )
        decision_summaries = [
            DecisionContextSummary(
                id=d.id,
                question_id=d.question_id,
                decision_type=d.decision_type,
                outcome=d.outcome,
                rationale=d.rationale,
                created_at=d.created_at,
            )
            for d in decisions_db
        ]
        entity_counts["decisions"] = len(decision_summaries)

        from sqlalchemy import or_
        review_filters = []
        if claim_ids:
            review_filters.append(Review.claim_id.in_(claim_ids))
        if run_ids:
            review_filters.append(Review.analysis_run_id.in_(run_ids))

        reviews_db: list[Review] = []
        if review_filters:
            reviews_db = db.query(Review).filter(or_(*review_filters)).all()

        review_summaries = [
            ReviewContextSummary(
                id=r.id,
                claim_id=r.claim_id,
                analysis_run_id=r.analysis_run_id,
                reviewer_role=r.reviewer_role,
                outcome=r.outcome,
                comments=r.comments,
                findings=r.findings,
            )
            for r in reviews_db
        ]
        entity_counts["reviews"] = len(review_summaries)


        # 8. Constraints, Confounders & Biases
        known_constraints: list[str] = []
        known_biases: list[str] = []
        unresolved_contradictions: list[str] = []

        if plan_summary:
            known_constraints.extend(plan_summary.potential_confounders)
            known_biases.extend(plan_summary.sources_of_bias)
            known_constraints.extend(plan_summary.limitations)

        # 9. Research Intelligence via Adaptive Orchestrator (Optional / Grounded)
        research_intel_payload: dict[str, Any] | None = None
        activated_layers: list[str] = []
        if activate_orchestrator:
            try:
                from src.services.orchestrator import assemble_intelligence_packet

                corpus = f"{project.title} {question.question}"
                if plan_summary and plan_summary.objective:
                    corpus += f" {plan_summary.objective}"

                packet = assemble_intelligence_packet(
                    db=db,
                    dwh_db=dwh_db,
                    project_id=project.id,
                    user_query=corpus,
                    project_context={"project_id": project.id, "title": project.title},
                )
                research_intel_payload = packet.model_dump()
                if packet.retrieval_summary:
                    activated_layers = [l.value for l in packet.retrieval_summary.activated_layers]
            except Exception:
                research_intel_payload = None

        latency_ms = round((time.time() - start_time) * 1000.0, 2)

        meta = ContextBuildMetadata(
            context_type=ScientificContextType.INVESTIGATION_PLANNING,
            latency_ms=latency_ms,
            entity_counts=entity_counts,
            missing_information=missing_info,
            activated_intelligence_layers=activated_layers,
        )

        ctx = InvestigationPlanningContext(
            project=project_summary,
            research_plan=plan_summary,
            research_question=q_summary,
            hypotheses=hypotheses_summaries,
            available_datasets=dataset_summaries,
            available_artifacts=artifact_summaries,
            previous_results=results_summaries,
            existing_evidence=evidence_summaries,
            claims=claim_summaries,
            decisions=decision_summaries,
            reviews=review_summaries,
            known_constraints=known_constraints,
            known_biases=known_biases,
            unresolved_contradictions=unresolved_contradictions,
            research_intelligence=research_intel_payload,
            missing_information=missing_info,
            provenance_records=provenance_records,
            metadata=meta,
        )

        # Calculate rendered size
        rendered = cls.format_investigation_planning_context_for_prompt(ctx)
        ctx.metadata.rendered_char_count = len(rendered)
        return ctx

    # --------------------------------------------------------------------------
    # 2. Future Context Contracts (Interfaces)
    # --------------------------------------------------------------------------
    @classmethod
    def build_capability_matching_context(
        cls,
        db: Session,
        question_id: int,
        step_goal: str,
        required_inputs: list[str] | None = None,
        required_outputs: list[str] | None = None,
        category: str | None = None,
    ) -> CapabilityMatchingContext:
        """
        Assembles filtered candidate capabilities matching an investigation step goal.
        """
        start_time = time.time()
        question = db.get(ResearchQuestion, question_id)
        if not question:
            raise ValueError(f"ResearchQuestion {question_id} not found")

        project = db.get(ResearchProject, question.project_id)
        if not project:
            raise ValueError(f"Project {question.project_id} not found")

        # Deterministic capability filtering (enabled only, optional category)
        stmt = select(ScientificCapability).join(ScientificApplication).where(
            ScientificCapability.is_enabled.is_(True),
            ScientificApplication.is_enabled.is_(True),
        )
        if category:
            stmt = stmt.where(ScientificApplication.category == category)
        caps = list(db.scalars(stmt).all())

        candidate_caps = [ScientificCapabilityResponse.model_validate(c) for c in caps]

        datasets_db = db.query(DatasetVersion).filter(DatasetVersion.project_id == project.id).all()
        dataset_summaries = [DatasetVersionContextSummary.model_validate(d) for d in datasets_db]

        latency_ms = round((time.time() - start_time) * 1000.0, 2)
        meta = ContextBuildMetadata(
            context_type=ScientificContextType.CAPABILITY_MATCHING,
            latency_ms=latency_ms,
            entity_counts={"capabilities": len(candidate_caps), "datasets": len(dataset_summaries)},
        )

        return CapabilityMatchingContext(
            project=ProjectContextSummary.model_validate(project),
            research_question=ResearchQuestionContextSummary(
                id=question.id, project_id=question.project_id, text=question.question, status=question.status
            ),
            investigation_step_goal=step_goal,
            required_input_types=required_inputs or [],
            required_output_types=required_outputs or [],
            available_datasets=dataset_summaries,
            candidate_capabilities=candidate_caps,
            methodological_constraints=[],
            missing_information=[] if candidate_caps else ["No registered capabilities matched the filters."],
            provenance_records=[
                ContextProvenanceRecord(
                    source_type="CAPABILITY_REGISTRY",
                    entity_type="ScientificCapability",
                    record_id="filtered_set",
                )
            ],
            metadata=meta,
        )

    @classmethod
    def build_experiment_planning_context(
        cls,
        db: Session,
        question_id: int | None = None,
        investigation_step_id: int | None = None,
        capability_key: str | None = None,
        hypothesis_id: int | None = None,
        dataset_version_id: int | None = None,
    ) -> ExperimentPlanningContext:
        """
        Assembles context for pre-specifying an Experiment (AnalysisPlan) from an InvestigationStep.
        """
        start_time = time.time()
        step: InvestigationStep | None = None
        if investigation_step_id:
            step = db.get(InvestigationStep, investigation_step_id)
            if not step:
                raise ValueError(f"InvestigationStep {investigation_step_id} not found")
            question_id = step.question_id

        if not question_id:
            raise ValueError("Either question_id or investigation_step_id must be provided")

        question = db.get(ResearchQuestion, question_id)
        if not question:
            raise ValueError(f"ResearchQuestion {question_id} not found")

        project = db.get(ResearchProject, question.project_id)
        if not project:
            raise ValueError(f"Project {question.project_id} not found")

        hypothesis_summary: HypothesisContextSummary | None = None
        if hypothesis_id:
            h = db.get(Hypothesis, hypothesis_id)
            if h:
                hypothesis_summary = HypothesisContextSummary(
                    id=h.id, question_id=h.question_id, statement=h.statement, status=h.status, rationale=h.rationale
                )
        else:
            # Pick first active hypothesis for question if present
            h_stmt = select(Hypothesis).where(Hypothesis.question_id == question.id)
            h = db.scalars(h_stmt).first()
            if h:
                hypothesis_summary = HypothesisContextSummary(
                    id=h.id, question_id=h.question_id, statement=h.statement, status=h.status, rationale=h.rationale
                )

        selected_cap_resp: ScientificCapabilityResponse | None = None
        if step:
            sel_stmt = select(CapabilitySelection).where(CapabilitySelection.investigation_step_id == step.id)
            selection = db.scalars(sel_stmt).first()
            if selection and selection.selected_capability_id:
                cap = db.get(ScientificCapability, selection.selected_capability_id)
                if cap:
                    selected_cap_resp = ScientificCapabilityResponse.model_validate(cap)

        if not selected_cap_resp and capability_key:
            stmt = select(ScientificCapability).where(ScientificCapability.capability_key == capability_key)
            cap = db.scalars(stmt).first()
            if cap:
                selected_cap_resp = ScientificCapabilityResponse.model_validate(cap)

        # Datasets
        dataset_summary: DatasetVersionContextSummary | None = None
        if dataset_version_id:
            ds = db.get(DatasetVersion, dataset_version_id)
            if ds:
                dataset_summary = DatasetVersionContextSummary.model_validate(ds)
        else:
            ds_stmt = select(DatasetVersion).where(DatasetVersion.project_id == project.id).order_by(desc(DatasetVersion.id))
            ds = db.scalars(ds_stmt).first()
            if ds:
                dataset_summary = DatasetVersionContextSummary.model_validate(ds)

        # Artifacts
        art_stmt = select(Artifact).where(Artifact.project_id == project.id)
        artifacts = list(db.scalars(art_stmt).all())
        artifact_summaries = [ArtifactContextSummary.model_validate(a) for a in artifacts]

        # Prior experiments
        plan_stmt = select(AnalysisPlan).join(ResearchQuestion).where(ResearchQuestion.project_id == project.id)
        prior_plans = list(db.scalars(plan_stmt).all())
        prior_exp_summaries = [
            {"id": p.id, "method": p.method, "parameters": p.parameters}
            for p in prior_plans
        ]

        missing_info: list[str] = []
        if not selected_cap_resp:
            missing_info.append("No ScientificCapability has been matched or assigned to this step.")
        if not dataset_summary and not artifact_summaries:
            missing_info.append("No DatasetVersions or prior Artifacts currently exist for this project.")

        latency_ms = round((time.time() - start_time) * 1000.0, 2)
        meta = ContextBuildMetadata(
            context_type=ScientificContextType.EXPERIMENT_PLANNING,
            latency_ms=latency_ms,
            entity_counts={
                "has_capability": int(selected_cap_resp is not None),
                "dataset_count": int(dataset_summary is not None),
                "artifact_count": len(artifact_summaries),
                "prior_experiment_count": len(prior_exp_summaries),
            },
        )

        return ExperimentPlanningContext(
            project=ProjectContextSummary.model_validate(project),
            research_question=ResearchQuestionContextSummary(
                id=question.id, project_id=question.project_id, text=question.question, status=question.status
            ),
            hypothesis=hypothesis_summary,
            selected_capability=selected_cap_resp,
            intended_dataset=dataset_summary,
            intended_artifacts=artifact_summaries,
            parameter_schema=selected_cap_resp.input_schema if selected_cap_resp else None,
            expected_outputs=[
                t if isinstance(t, str) else str(t.get("semantic_type", t))
                for t in (selected_cap_resp.output_types or [])
            ] if selected_cap_resp else [],
            previous_experiments=prior_exp_summaries,
            missing_information=missing_info,
            provenance_records=[],
            metadata=meta,
        )

    @classmethod
    def build_result_interpretation_context(
        cls,
        db: Session,
        analysis_run_id: int,
    ) -> ResultInterpretationContext:
        """
        Assembles context for interpreting real results from a completed Experiment Run.
        """
        start_time = time.time()
        run = db.get(AnalysisRun, analysis_run_id)
        if not run:
            raise ValueError(f"AnalysisRun {analysis_run_id} not found")

        plan = db.get(AnalysisPlan, run.analysis_plan_id)
        if not plan:
            raise ValueError(f"AnalysisPlan {run.analysis_plan_id} not found")

        question = db.get(ResearchQuestion, plan.question_id)
        if not question:
            raise ValueError(f"ResearchQuestion {plan.question_id} not found")

        project = db.get(ResearchProject, question.project_id)
        if not project:
            raise ValueError(f"Project {question.project_id} not found")

        hypothesis_summary: HypothesisContextSummary | None = None
        if plan.hypothesis_id:
            h = db.get(Hypothesis, plan.hypothesis_id)
            if h:
                hypothesis_summary = HypothesisContextSummary(
                    id=h.id, question_id=h.question_id, statement=h.statement, status=h.status
                )

        results_db = db.query(Result).filter(Result.analysis_run_id == run.id).all()
        result_summaries = [ResultContextSummary.model_validate(r) for r in results_db]

        artifacts_db = db.query(Artifact).filter(Artifact.analysis_run_id == run.id).all()
        artifact_summaries = [ArtifactContextSummary.model_validate(a) for a in artifacts_db]

        dataset_summary: DatasetVersionContextSummary | None = None
        if run.dataset_version_id:
            ds = db.get(DatasetVersion, run.dataset_version_id)
            if ds:
                dataset_summary = DatasetVersionContextSummary.model_validate(ds)

        missing_info: list[str] = []
        if run.status != "completed":
            missing_info.append(f"Execution status is '{run.status}', not completed. Empirical outputs may be partial.")
        if not result_summaries:
            missing_info.append("No Result records registered for this run.")

        latency_ms = round((time.time() - start_time) * 1000.0, 2)
        meta = ContextBuildMetadata(
            context_type=ScientificContextType.RESULT_INTERPRETATION,
            latency_ms=latency_ms,
            entity_counts={"results": len(result_summaries), "artifacts": len(artifact_summaries)},
        )

        return ResultInterpretationContext(
            project=ProjectContextSummary.model_validate(project),
            research_question=ResearchQuestionContextSummary(
                id=question.id, project_id=question.project_id, text=question.question, status=question.status
            ),
            hypothesis=hypothesis_summary,
            analysis_plan_id=plan.id,
            analysis_run_id=run.id,
            run_status=run.status,
            actual_parameters=run.parameters,
            dataset_version=dataset_summary,
            results=result_summaries,
            artifacts=artifact_summaries,
            missing_information=missing_info,
            provenance_records=[
                ContextProvenanceRecord(
                    source_type="ANALYSIS_EXECUTION_STATE",
                    entity_type="AnalysisRun",
                    record_id=run.id,
                    notes=f"Status: {run.status}",
                )
            ],
            metadata=meta,
        )

    # --------------------------------------------------------------------------
    # 3. Prompt Rendering
    # --------------------------------------------------------------------------
    @classmethod
    def format_investigation_planning_context_for_prompt(
        cls,
        ctx: InvestigationPlanningContext,
    ) -> str:
        """
        Renders the structured InvestigationPlanningContext into clear,
        provenance-segregated prompt sections for the LLM Gateway.
        """
        sections: list[str] = [
            "================================================================================",
            "INVESTIGATION PLANNING CONTEXT (SCIENTIFIC WORKFLOW REASONING)",
            "================================================================================",
            f"Context Type: {ctx.metadata.context_type.value.upper()}",
            f"Assembly Latency: {ctx.metadata.latency_ms} ms",
            "",
        ]

        # 1. Project
        sections.append("--- 1. RESEARCH PROJECT [PROVENANCE: DATABASE_WORLD_MODEL] ---")
        sections.append(f"[FACT] Project #{ctx.project.id}: {ctx.project.title}")
        if ctx.project.description:
            sections.append(f"[FACT] Description: {ctx.project.description}")
        if ctx.project.objective:
            sections.append(f"[FACT] Objective: {ctx.project.objective}")
        sections.append("")

        # 2. Approved Research Plan
        sections.append("--- 2. APPROVED RESEARCH PLAN [PROVENANCE: RESEARCH_PLAN] ---")
        if ctx.research_plan:
            rp = ctx.research_plan
            sections.append(f"[RESEARCH PLAN] Plan #{rp.id} (v{rp.version}, Status: {rp.status.upper()}): {rp.title}")
            if rp.objective:
                sections.append(f"[RESEARCH PLAN] Core Objective: {rp.objective}")
            if rp.scientific_background:
                sections.append(f"[RESEARCH PLAN] Scientific Background: {rp.scientific_background}")
            if rp.proposed_strategy:
                sections.append(f"[RESEARCH PLAN] Proposed Strategy: {rp.proposed_strategy}")
            if rp.evidence_required:
                sections.append("[RESEARCH PLAN] Evidence Required:")
                for ev in rp.evidence_required:
                    sections.append(f"  * {ev}")
            if rp.analytical_stages:
                sections.append("[RESEARCH PLAN] Planned Analytical Stages:")
                for st in rp.analytical_stages:
                    st_name = st.get("name") or st.get("stage") or "Stage"
                    st_desc = st.get("description") or ""
                    sections.append(f"  * {st_name}: {st_desc}")
            if rp.validation_strategy:
                sections.append(f"[RESEARCH PLAN] Validation Strategy: {rp.validation_strategy}")
            if rp.interpretation_criteria:
                sections.append(f"[RESEARCH PLAN] Interpretation Criteria: {rp.interpretation_criteria}")
        else:
            sections.append("[NO APPROVED RESEARCH PLAN]: No ResearchPlan is linked to this project. (Reason from question and data facts directly).")
        sections.append("")

        # 3. Focal Research Question
        sections.append("--- 3. FOCAL RESEARCH QUESTION [PROVENANCE: RESEARCH_QUESTION] ---")
        sections.append(f"[FACT] Question #{ctx.research_question.id}: \"{ctx.research_question.text}\"")
        if ctx.research_question.status:
            sections.append(f"[FACT] Question Status: {ctx.research_question.status}")
        if ctx.research_question.inferential_level:
            sections.append(f"[FACT] Inferential Level: {ctx.research_question.inferential_level}")
        sections.append("")

        # 4. Related Hypotheses & Predictions
        sections.append("--- 4. RELATED HYPOTHESES & PREDICTIONS [PROVENANCE: HYPOTHESIS] ---")
        if ctx.hypotheses:
            for h in ctx.hypotheses:
                status_str = f" [{h.status.upper()}]" if h.status else ""
                sections.append(f"[HYPOTHESIS #{h.id}]{status_str} Statement: {h.statement}")
                if h.rationale:
                    sections.append(f"  Rationale: {h.rationale}")
                if h.predictions:
                    for p in h.predictions:
                        sections.append(f"  ↳ [PREDICTION #{p.id}]: {p.statement}")
        else:
            sections.append("[NO RELATED HYPOTHESES]: No specific candidate hypotheses are stored for this question.")
        sections.append("")

        # 5. Available Datasets & Artifacts
        sections.append("--- 5. AVAILABLE SCIENTIFIC DATASETS & INPUT ARTIFACTS [PROVENANCE: DATASET_VERSION] ---")
        if ctx.available_datasets:
            for ds in ctx.available_datasets:
                mbr_str = f", {ds.member_count} items" if ds.member_count is not None else ""
                sha_str = f" [SHA256: {ds.manifest_sha256[:12]}...]" if ds.manifest_sha256 else ""
                sections.append(f"[FACT] DatasetVersion #{ds.id} ({ds.version_key}): Source '{ds.source_system}'{mbr_str}{sha_str}")
        else:
            sections.append("[NO DATASET INFORMATION]: No frozen DatasetVersions are registered in this project.")

        if ctx.available_artifacts:
            sections.append("[FACT] Available Derived Artifacts:")
            for art in ctx.available_artifacts:
                sections.append(f"  * Artifact #{art.id} ({art.artifact_type}) [URI: {art.uri}]")
        sections.append("")

        # 6. Previous Results & Existing Evidence
        sections.append("--- 6. PREVIOUS RESULTS & SCIENTIFIC EVIDENCE [PROVENANCE: RESULT / EVIDENCE] ---")
        if ctx.previous_results:
            for res in ctx.previous_results:
                run_ref = f" (Run #{res.analysis_run_id})" if res.analysis_run_id else ""
                sections.append(f"[PREVIOUS RESULT #{res.id}]{run_ref} Type: {res.result_type} | Summary: {res.summary or 'N/A'}")
        else:
            sections.append("[NO PREVIOUS RESULTS]: No computational runs have generated empirical results for this question yet.")

        if ctx.existing_evidence:
            sections.append("[FACT] Evidence Items:")
            for ev in ctx.existing_evidence:
                sections.append(f"  * Evidence #{ev.id} (Claim #{ev.claim_id}): Direction '{ev.direction}', Status '{ev.validity_status}' — {ev.summary or 'No summary'}")
        sections.append("")

        # 7. Claims, Decisions & Reviews
        sections.append("--- 7. CLAIMS & IMPORTANT DECISIONS [PROVENANCE: CLAIM / DECISION] ---")
        if ctx.claims:
            for clm in ctx.claims:
                sections.append(f"[CLAIM #{clm.id}] ({clm.claim_type}, Status: {clm.epistemic_status}): {clm.text}")
        if ctx.decisions:
            for dec in ctx.decisions:
                sections.append(f"[DECISION #{dec.id}] ({dec.decision_type}): Outcome '{dec.outcome}' — {dec.rationale or 'N/A'}")
        if ctx.reviews:
            for rev in ctx.reviews:
                sections.append(f"[REVIEW #{rev.id}] ({rev.reviewer_role}): Outcome '{rev.outcome}' — {rev.comments or 'N/A'}")
        if not ctx.claims and not ctx.decisions and not ctx.reviews:
            sections.append("[NO PRIOR CLAIMS/DECISIONS]: No formal claims, decisions, or reviews recorded.")
        sections.append("")

        # 8. Constraints, Confounders & Biases
        sections.append("--- 8. CONSTRAINTS, CONFOUNDERS & KNOWN BIASES ---")
        has_constraints = False
        if ctx.known_constraints:
            has_constraints = True
            sections.append("[CONSTRAINT] Methodological / Scientific Constraints:")
            for c in ctx.known_constraints:
                sections.append(f"  * {c}")
        if ctx.known_biases:
            has_constraints = True
            sections.append("[BIAS WARNING] Known Sources of Sampling or Measurement Bias:")
            for b in ctx.known_biases:
                sections.append(f"  * {b}")
        if not has_constraints:
            sections.append("[NO EXPLICIT CONSTRAINTS RECORDED]")
        sections.append("")

        # 9. Research Intelligence (Optional Packet)
        if ctx.research_intelligence:
            from src.schemas.intelligence_packet import ResearchIntelligencePacket
            from src.services.orchestrator import format_packet_for_llm_prompt

            try:
                packet = ResearchIntelligencePacket.model_validate(ctx.research_intelligence)
                intel_rendered = format_packet_for_llm_prompt(packet)
                sections.append("--- 9. GROUNDED RESEARCH INTELLIGENCE (DWH OCCURRENCES & TAXONOMY) ---")
                sections.append(intel_rendered)
                sections.append("")
            except Exception:
                pass

        # 10. Missing Information & Absence of Evidence
        sections.append("--- 10. EXPLICIT ABSENCE OF EVIDENCE / MISSING INFORMATION ---")
        if ctx.missing_information:
            for mi in ctx.missing_information:
                sections.append(f"⚠️ [MISSING INFO]: {mi}")
        else:
            sections.append("All primary scientific context components were successfully located.")
        sections.append("")

        # 11. LLM Reasoning Instructions
        sections.append("--- 11. INVESTIGATION PLANNING TASK INSTRUCTIONS ---")
        sections.append("Based on the approved ResearchPlan, focal question, and empirical facts above:")
        sections.append("1. Propose concrete, reproducible scientific steps required to answer this question.")
        sections.append("2. Sequence steps logically (e.g. data audit -> representation extraction -> statistical test -> robustness check).")
        sections.append("3. Reference the exact datasets and empirical constraints specified above; do NOT invent ungrounded data.")
        sections.append("4. Strictly distinguish [FACT], [PREVIOUS RESULT], and [RESEARCH PLAN] from your [LLM INTERPRETATION].")
        sections.append("================================================================================")

        return "\n".join(sections)

    @classmethod
    def format_capability_matching_context_for_prompt(
        cls,
        ctx: CapabilityMatchingContext,
    ) -> str:
        """
        Renders the CapabilityMatchingContext into a clean prompt context for Phase 9 capability selection.
        """
        sections: list[str] = [
            "================================================================================",
            "SCIENTIFIC CAPABILITY MATCHING CONTEXT (PHASE 9 TOOL SELECTION)",
            "================================================================================",
            f"Focal Research Question #{ctx.research_question.id}: \"{ctx.research_question.text}\"",
            f"Target Investigation Step Goal: {ctx.investigation_step_goal}",
            "",
            "--- CANDIDATE REGISTERED SCIENTIFIC CAPABILITIES ---",
        ]
        if ctx.candidate_capabilities:
            for c in ctx.candidate_capabilities:
                sections.append(
                    f"- [{c.capability_key}] \"{c.display_name}\"\n"
                    f"  * Scientific Purpose: {c.scientific_purpose}\n"
                    f"  * Category/Tasks: {c.scientific_tasks or 'general'}\n"
                    f"  * Reproducibility: {c.reproducibility_level} | Duration: {c.typical_duration or 'N/A'}"
                )
        else:
            sections.append("No candidate capabilities supplied.")

        sections.append("================================================================================")
        return "\n".join(sections)

    @classmethod
    def format_experiment_planning_context_for_prompt(
        cls,
        ctx: ExperimentPlanningContext,
    ) -> str:
        """
        Renders the ExperimentPlanningContext into a structured prompt context with strict provenance tagging.
        """
        sections: list[str] = [
            "================================================================================",
            "SCIENTIFIC EXPERIMENT PLANNING CONTEXT (LLM STAGE 4 — EXPERIMENT DESIGN)",
            "================================================================================",
            f"[FACT] Project #{ctx.project.id}: \"{ctx.project.title}\"",
            f"[FACT] Project Objective: {ctx.project.objective or 'N/A'}",
            f"[FACT] Focal Research Question #{ctx.research_question.id}: \"{ctx.research_question.text}\"",
        ]

        if ctx.hypothesis:
            sections.append(f"[FACT] Focal Hypothesis #{ctx.hypothesis.id}: \"{ctx.hypothesis.statement}\"")
            if ctx.hypothesis.rationale:
                sections.append(f"[FACT] Hypothesis Rationale: {ctx.hypothesis.rationale}")
        sections.append("")

        # Selected Capability
        sections.append("--- 2. SELECTED SCIENTIFIC CAPABILITY & PARAMETER SCHEMA ---")
        if ctx.selected_capability:
            cap = ctx.selected_capability
            sections.append(f"[CAPABILITY_CONTRACT] Key: {cap.capability_key} | Display: \"{cap.display_name}\"")
            sections.append(f"[CAPABILITY_CONTRACT] Purpose: {cap.scientific_purpose}")
            sections.append(f"[CAPABILITY_CONTRACT] Tasks: {cap.scientific_tasks or 'General'}")
            in_types = ", ".join(t if isinstance(t, str) else str(t.get("semantic_type", t)) for t in (cap.input_types or []))
            out_types = ", ".join(t if isinstance(t, str) else str(t.get("semantic_type", t)) for t in (cap.output_types or []))
            sections.append(f"[CAPABILITY_CONTRACT] Input Types: {in_types or 'None'}")
            sections.append(f"[CAPABILITY_CONTRACT] Output Types: {out_types or 'None'}")
            sections.append(f"[CAPABILITY_CONTRACT] Reproducibility: {cap.reproducibility_level}")
            if ctx.parameter_schema:
                sections.append(f"[CAPABILITY_SCHEMA] Declared Input Parameter Schema:\n{ctx.parameter_schema}")
            else:
                sections.append("[CAPABILITY_SCHEMA] Standard parameters (no rigid JSON schema constraint declared).")
        else:
            sections.append("[NO CAPABILITY SELECTED]: No specific capability has been bound.")
        sections.append("")

        # Datasets
        sections.append("--- 3. AVAILABLE DATASET VERSIONS [PROVENANCE: DATASET_VERSION] ---")
        if ctx.intended_dataset:
            ds = ctx.intended_dataset
            sections.append(f"[DATASET_VERSION #{ds.id}] Key: \"{ds.version_key}\" | Source: {ds.source_system} | Records: {ds.member_count or 'N/A'}")
        else:
            sections.append("[NO DATASETS]: No registered dataset versions found in project.")
        sections.append("")

        # Artifacts
        sections.append("--- 4. AVAILABLE PRIOR ARTIFACTS [PROVENANCE: ARTIFACT] ---")
        if ctx.intended_artifacts:
            for art in ctx.intended_artifacts:
                sections.append(f"[ARTIFACT #{art.id}] Type: {art.artifact_type} | URI: {art.uri}")
        else:
            sections.append("[NO PRIOR ARTIFACTS]: No previous artifact outputs exist.")
        sections.append("")

        # Previous experiments
        sections.append("--- 5. PRIOR EXPERIMENTS RECORDED IN PROJECT ---")
        if ctx.previous_experiments:
            for exp in ctx.previous_experiments:
                sections.append(f"[PRIOR EXPERIMENT #{exp.get('id')}] Title: \"{exp.get('title')}\" | Method: {exp.get('methodology')}")
        else:
            sections.append("[NO PRIOR EXPERIMENTS]: This is the first experiment planned for this scope.")
        sections.append("")

        # Missing info
        sections.append("--- 6. KNOWN LIMITATIONS & MISSING INFORMATION ---")
        if ctx.missing_information:
            for mi in ctx.missing_information:
                sections.append(f"⚠️ [MISSING INFO]: {mi}")
        else:
            sections.append("All primary context items were located.")
        sections.append("")

        sections.append("================================================================================")
        return "\n".join(sections)

