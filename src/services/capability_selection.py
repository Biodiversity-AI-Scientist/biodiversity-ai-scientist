"""
Phase 9: Scientific Capability Matching & Selection Service
Handles deterministic eligibility filtering, single-option auto selection,
LLM comparative selection, CapabilityGap tracking, and multi-factor readiness.
"""

from datetime import datetime
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.llm.contracts import CapabilitySelectionLLMInput, CapabilitySelectionLLMOutput
from src.llm.gateway import LLMGateway
from src.models.investigation_step import (
    InvestigationPlanGeneration,
    InvestigationStep,
    InvestigationStepDependency,
)
from src.models.research_project import ResearchProject
from src.models.research_question import ResearchQuestion
from src.models.scientific_capability import (
    CapabilityGap,
    CapabilitySelection,
    ScientificApplication,
    ScientificCapability,
)
from src.schemas.scientific_capability import (
    CapabilityGapResponse,
    CapabilityGapUpdateRequest,
    CapabilitySelectionOverrideRequest,
    CapabilitySelectionResponse,
    ScientificCapabilityResponse,
)
from src.services.scientific_context import ScientificContextService

logger = logging.getLogger(__name__)


def compute_step_readiness(db: Session, step: InvestigationStep) -> tuple[str, bool]:
    """
    Computes the multi-factor readiness state and derived is_blocked boolean.
    Taxonomy: 'ready', 'dependency_blocked', 'capability_blocked', 'awaiting_human', 'awaiting_external_evidence'.
    """
    if step.status == "completed" or step.status == "skipped" or step.status == "rejected":
        return "ready", False

    # 1. Dependency Prerequisite check
    dep_rows = (
        db.query(InvestigationStepDependency)
        .filter(InvestigationStepDependency.step_id == step.id)
        .all()
    )
    if dep_rows:
        prereq_ids = [d.depends_on_step_id for d in dep_rows]
        uncompleted_prereqs = (
            db.query(InvestigationStep)
            .filter(
                InvestigationStep.id.in_(prereq_ids),
                InvestigationStep.status != "completed",
            )
            .count()
        )
        if uncompleted_prereqs > 0:
            return "dependency_blocked", True

    # 2. Capability availability check
    if step.requires_capability:
        selection = (
            db.query(CapabilitySelection)
            .filter(CapabilitySelection.investigation_step_id == step.id)
            .first()
        )
        if not selection:
            # Not yet matched
            return "capability_blocked", True
        if selection.selection_method == "none_adequate" or selection.selected_capability_id is None:
            return "capability_blocked", True

        # Check if unresolved capability gap exists
        unresolved_gap = (
            db.query(CapabilityGap)
            .filter(
                CapabilityGap.investigation_step_id == step.id,
                CapabilityGap.status.in_(["unresolved", "in_progress"]),
            )
            .first()
        )
        if unresolved_gap:
            return "capability_blocked", True

    return "ready", False


class CapabilitySelectionService:
    @classmethod
    def match_capability_for_step(
        cls,
        db: Session,
        step_id: int,
        user_guidance: str | None = None,
        gateway: LLMGateway | None = None,
    ) -> CapabilitySelectionResponse:
        """
        Executes the Phase 9 Capability Matching pipeline for an InvestigationStep:
        1. Deterministic eligibility filtering
        2. Sole-option auto selection or Gap generation
        3. LLM comparative selection when multiple eligible tools exist
        """
        step = db.get(InvestigationStep, step_id)
        if not step:
            raise ValueError(f"InvestigationStep #{step_id} not found")

        generation = db.get(InvestigationPlanGeneration, step.generation_id)
        if not generation:
            raise ValueError(f"InvestigationPlanGeneration #{step.generation_id} not found")

        question = db.get(ResearchQuestion, generation.question_id)
        if not question:
            raise ValueError(f"ResearchQuestion #{generation.question_id} not found")

        # If step doesn't require capability
        if not step.requires_capability:
            selection = (
                db.query(CapabilitySelection)
                .filter(CapabilitySelection.investigation_step_id == step.id)
                .first()
            )
            if not selection:
                selection = CapabilitySelection(
                    investigation_step_id=step.id,
                    selected_capability_id=None,
                    eligible_capability_ids=[],
                    selection_method="not_required",
                    scientific_rationale="Step does not require an external computational capability or tool.",
                    rejected_alternatives=[],
                    known_limitations=None,
                    researcher_status="approved",
                )
                db.add(selection)
                db.commit()
                db.refresh(selection)
            return CapabilitySelectionResponse.model_validate(selection)

        # 1. Deterministic Eligibility Filter
        all_caps = (
            db.query(ScientificCapability)
            .join(ScientificApplication)
            .filter(
                ScientificCapability.is_enabled.is_(True),
                ScientificApplication.is_enabled.is_(True),
            )
            .all()
        )

        eligible_caps: list[ScientificCapability] = []
        step_text_lower = f"{step.title} {step.scientific_goal} {step.step_type} {step.required_operation or ''}".lower()

        for cap in all_caps:
            app = cap.application
            # Match heuristics based on scientific task keywords, categories, or capability keys
            cap_text = f"{cap.capability_key} {cap.display_name} {cap.scientific_purpose} {cap.scientific_tasks or ''} {app.category}".lower()

            is_match = False
            # Check domain semantic alignment
            if "worms" in step_text_lower or "taxa" in step_text_lower or "taxonomy" in step_text_lower:
                if "worms" in cap_text or "taxonomy" in cap_text or "taxa" in cap_text:
                    is_match = True
            elif "dinov3" in step_text_lower or "embedding" in step_text_lower or "representation" in step_text_lower:
                if "dinov3" in cap_text or "embedding" in cap_text or "representation" in cap_text:
                    is_match = True
            elif "classifier" in step_text_lower or "classification" in step_text_lower or "training" in step_text_lower or "cnn" in step_text_lower:
                if "classifier" in cap_text or "classification" in cap_text or "training" in cap_text or "cnn" in cap_text:
                    is_match = True
            elif "permanova" in step_text_lower or "statistic" in step_text_lower or "morphometric" in step_text_lower:
                if "permanova" in cap_text or "statistic" in cap_text or "morphometric" in cap_text:
                    is_match = True
            elif "literature" in step_text_lower or "search" in step_text_lower:
                if "literature" in cap_text or "arxiv" in cap_text or "biorxiv" in cap_text or "search" in cap_text:
                    is_match = True
            else:
                # General semantic overlap using token set matching
                import re
                cap_tokens = set(re.findall(r"\w+", cap_text))
                words = [w for w in step.step_type.lower().split("_") if len(w) > 3]
                if any(w in cap_tokens for w in words):
                    is_match = True

            if is_match:
                eligible_caps.append(cap)

        # Retrieve existing selection if any
        selection = (
            db.query(CapabilitySelection)
            .filter(CapabilitySelection.investigation_step_id == step.id)
            .first()
        )
        if not selection:
            selection = CapabilitySelection(investigation_step_id=step.id)
            db.add(selection)

        selection.eligible_capability_ids = [c.id for c in eligible_caps]

        # 2. Decision Dispatch
        if len(eligible_caps) == 0:
            # Case 0: Capability Gap
            selection.selected_capability_id = None
            selection.selection_method = "none_adequate"
            selection.scientific_rationale = (
                f"No registered capability matches the required scientific operation: '{step.required_operation or step.scientific_goal}'. "
                "A CapabilityGap record has been logged."
            )
            selection.rejected_alternatives = []
            selection.known_limitations = "Execution blocked pending adapter development or external manual import."
            selection.researcher_status = "proposed"

            # Create or update CapabilityGap
            gap = (
                db.query(CapabilityGap)
                .filter(CapabilityGap.investigation_step_id == step.id)
                .first()
            )
            if not gap:
                gap = CapabilityGap(
                    project_id=generation.project_id,
                    investigation_step_id=step.id,
                    scientific_requirement=f"{step.title}: {step.scientific_goal}",
                    reason_unavailable=f"No enabled capability in registry provides {step.step_type} operation for '{step.required_operation or step.title}'.",
                    possible_resolution="adapter_development",
                    status="unresolved",
                )
                db.add(gap)
            else:
                gap.status = "unresolved"

        elif len(eligible_caps) == 1:
            # Case 1: Sole eligible option (Deterministic auto-selection)
            sole_cap = eligible_caps[0]
            selection.selected_capability_id = sole_cap.id
            selection.selection_method = "deterministic_sole_option"
            selection.scientific_rationale = (
                f"Selected '{sole_cap.display_name}' ({sole_cap.capability_key}) as the sole eligible capability providing "
                f"{sole_cap.scientific_purpose}."
            )
            selection.rejected_alternatives = []
            selection.known_limitations = None
            selection.researcher_status = "proposed"

            # Resolve any existing gap
            gap = (
                db.query(CapabilityGap)
                .filter(CapabilityGap.investigation_step_id == step.id)
                .first()
            )
            if gap and gap.status == "unresolved":
                gap.status = "resolved"
                gap.resolved_at = datetime.utcnow()
                gap.resolution_notes = f"Resolved via deterministic selection of {sole_cap.capability_key}."

        else:
            # Case >1: Multiple candidates -> LLM Comparative Selection
            if gateway is None:
                gateway = LLMGateway()

            matching_context = ScientificContextService.build_capability_matching_context(
                db=db,
                question_id=generation.question_id,
                step_goal=step.scientific_goal,
                required_inputs=[step.required_operation] if step.required_operation else None,
            )
            rendered_ctx = ScientificContextService.format_capability_matching_context_for_prompt(matching_context)

            llm_input = CapabilitySelectionLLMInput(
                rendered_context=rendered_ctx,
                step_goal=step.scientific_goal,
                required_operation=step.required_operation,
                user_guidance=user_guidance,
            )

            try:
                res = gateway.invoke(
                    template_id="capability_comparative_selection_v1",
                    inputs=llm_input.model_dump(),
                )
                llm_output = CapabilitySelectionLLMOutput.model_validate(res.output)
                prov = res.metadata

                # Match selected key to DB object
                selected_cap = next(
                    (c for c in eligible_caps if c.capability_key == llm_output.selected_capability_key),
                    eligible_caps[0],
                )

                selection.selected_capability_id = selected_cap.id
                selection.selection_method = "llm_comparative_selection"
                selection.scientific_rationale = llm_output.scientific_rationale
                selection.rejected_alternatives = [
                    {"capability_key": r.capability_key, "rejection_reason": r.rejection_reason}
                    for r in llm_output.rejected_alternatives
                ]
                selection.known_limitations = llm_output.known_limitations
                selection.researcher_status = "proposed"
                selection.llm_provenance = {
                    "model": prov.model,
                    "confidence_score": llm_output.confidence_score,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Resolve any existing gap
                gap = (
                    db.query(CapabilityGap)
                    .filter(CapabilityGap.investigation_step_id == step.id)
                    .first()
                )
                if gap and gap.status == "unresolved":
                    gap.status = "resolved"
                    gap.resolved_at = datetime.utcnow()
                    gap.resolution_notes = f"Resolved via LLM selection of {selected_cap.capability_key}."

            except Exception as e:
                logger.warning("LLM comparative capability selection failed, falling back to first candidate: %s", e)
                fallback_cap = eligible_caps[0]
                selection.selected_capability_id = fallback_cap.id
                selection.selection_method = "deterministic_sole_option"
                selection.scientific_rationale = (
                    f"Selected '{fallback_cap.display_name}' ({fallback_cap.capability_key}) from {len(eligible_caps)} eligible options (fallback)."
                )
                selection.rejected_alternatives = [
                    {"capability_key": c.capability_key, "rejection_reason": "Not selected during fallback"}
                    for c in eligible_caps
                    if c.id != fallback_cap.id
                ]
                selection.researcher_status = "proposed"

        db.commit()
        db.refresh(selection)
        return CapabilitySelectionResponse.model_validate(selection)

    @classmethod
    def override_capability_selection(
        cls,
        db: Session,
        step_id: int,
        override_req: CapabilitySelectionOverrideRequest,
    ) -> CapabilitySelectionResponse:
        """
        Allows a human researcher to override or manually assign capability selection.
        """
        step = db.get(InvestigationStep, step_id)
        if not step:
            raise ValueError(f"InvestigationStep #{step_id} not found")

        selection = (
            db.query(CapabilitySelection)
            .filter(CapabilitySelection.investigation_step_id == step.id)
            .first()
        )
        if not selection:
            selection = CapabilitySelection(investigation_step_id=step.id)
            db.add(selection)

        if override_req.selected_capability_id is not None:
            cap = db.get(ScientificCapability, override_req.selected_capability_id)
            if not cap:
                raise ValueError(f"ScientificCapability #{override_req.selected_capability_id} not found")
            selection.selected_capability_id = cap.id
            selection.selection_method = "manual_researcher_selection"
            selection.scientific_rationale = override_req.scientific_rationale
            selection.researcher_status = override_req.researcher_status
        else:
            # Marked as gap manually
            selection.selected_capability_id = None
            selection.selection_method = "none_adequate"
            selection.scientific_rationale = override_req.scientific_rationale
            selection.researcher_status = override_req.researcher_status

        db.commit()
        db.refresh(selection)
        return CapabilitySelectionResponse.model_validate(selection)

    @classmethod
    def match_all_capabilities_for_question(
        cls,
        db: Session,
        question_id: int,
        user_guidance: str | None = None,
        gateway: LLMGateway | None = None,
    ) -> list[CapabilitySelectionResponse]:
        """
        Batch capability matching across all active InvestigationSteps for a question.
        """
        generation = (
            db.query(InvestigationPlanGeneration)
            .filter(InvestigationPlanGeneration.question_id == question_id)
            .order_by(InvestigationPlanGeneration.id.desc())
            .first()
        )
        if not generation:
            raise ValueError(f"No InvestigationPlanGeneration found for Question #{question_id}")

        steps = (
            db.query(InvestigationStep)
            .filter(InvestigationStep.generation_id == generation.id)
            .order_by(InvestigationStep.display_order.asc())
            .all()
        )

        results = []
        for s in steps:
            sel = cls.match_capability_for_step(
                db=db,
                step_id=s.id,
                user_guidance=user_guidance,
                gateway=gateway,
            )
            results.append(sel)
        return results

    @classmethod
    def get_capability_selection_for_step(
        cls,
        db: Session,
        step_id: int,
    ) -> CapabilitySelectionResponse | None:
        selection = (
            db.query(CapabilitySelection)
            .filter(CapabilitySelection.investigation_step_id == step_id)
            .first()
        )
        if not selection:
            return None
        return CapabilitySelectionResponse.model_validate(selection)

    @classmethod
    def list_capability_gaps(
        cls,
        db: Session,
        project_id: int,
    ) -> list[CapabilityGapResponse]:
        gaps = (
            db.query(CapabilityGap)
            .filter(CapabilityGap.project_id == project_id)
            .order_by(CapabilityGap.created_at.desc())
            .all()
        )
        return [CapabilityGapResponse.model_validate(g) for g in gaps]

    @classmethod
    def update_capability_gap(
        cls,
        db: Session,
        gap_id: int,
        update_req: CapabilityGapUpdateRequest,
    ) -> CapabilityGapResponse:
        gap = db.get(CapabilityGap, gap_id)
        if not gap:
            raise ValueError(f"CapabilityGap #{gap_id} not found")

        gap.status = update_req.status
        if update_req.possible_resolution:
            gap.possible_resolution = update_req.possible_resolution
        if update_req.resolution_notes:
            gap.resolution_notes = update_req.resolution_notes
        if update_req.resolved or update_req.status == "resolved":
            gap.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(gap)
        return CapabilityGapResponse.model_validate(gap)
