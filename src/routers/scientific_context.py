from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import get_db, get_dwh_db
from src.schemas.scientific_context import (
    CapabilityMatchingContext,
    ExperimentPlanningContext,
    InvestigationPlanningContext,
    ResultInterpretationContext,
)
from src.services.scientific_context import ScientificContextService

router = APIRouter(
    prefix="/context",
    tags=["Scientific Context Service"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]

DwhSession = Annotated[
    Session | None,
    Depends(get_dwh_db),
]


class InvestigationPlanningInspectRequest(BaseModel):
    question_id: int
    research_plan_id: int | None = None
    activate_orchestrator: bool = True


class InvestigationPlanningInspectResponse(BaseModel):
    context: InvestigationPlanningContext
    rendered_prompt: str


class CapabilityMatchingInspectRequest(BaseModel):
    question_id: int
    step_goal: str
    required_inputs: list[str] = []
    required_outputs: list[str] = []
    category: str | None = None


class ExperimentPlanningInspectRequest(BaseModel):
    question_id: int
    capability_key: str | None = None
    hypothesis_id: int | None = None
    dataset_version_id: int | None = None


class ResultInterpretationInspectRequest(BaseModel):
    analysis_run_id: int


@router.get(
    "/investigation-planning/{question_id}",
    response_model=InvestigationPlanningInspectResponse,
    summary="Get Investigation Planning Context for a Research Question",
)
def get_investigation_planning_context(
    question_id: int,
    db: DbSession,
    dwh_db: DwhSession = None,
    plan_id: int | None = Query(default=None, description="Optional specific ResearchPlan ID"),
    orchestrator: bool = Query(default=True, description="Activate Adaptive Research Intelligence Orchestrator"),
):
    try:
        ctx = ScientificContextService.build_investigation_planning_context(
            db=db,
            dwh_db=dwh_db,
            question_id=question_id,
            research_plan_id=plan_id,
            activate_orchestrator=orchestrator,
        )
        rendered = ScientificContextService.format_investigation_planning_context_for_prompt(ctx)
        return InvestigationPlanningInspectResponse(
            context=ctx,
            rendered_prompt=rendered,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Context building failed: {e}",
        )


@router.post(
    "/investigation-planning/inspect",
    response_model=InvestigationPlanningInspectResponse,
    summary="Inspect Investigation Planning Context with parameters",
)
def inspect_investigation_planning_context(
    req: InvestigationPlanningInspectRequest,
    db: DbSession,
    dwh_db: DwhSession = None,
):
    try:
        ctx = ScientificContextService.build_investigation_planning_context(
            db=db,
            dwh_db=dwh_db,
            question_id=req.question_id,
            research_plan_id=req.research_plan_id,
            activate_orchestrator=req.activate_orchestrator,
        )
        rendered = ScientificContextService.format_investigation_planning_context_for_prompt(ctx)
        return InvestigationPlanningInspectResponse(
            context=ctx,
            rendered_prompt=rendered,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/capability-matching/inspect",
    response_model=CapabilityMatchingContext,
    summary="Inspect Capability Matching Context",
)
def inspect_capability_matching_context(
    req: CapabilityMatchingInspectRequest,
    db: DbSession,
):
    try:
        return ScientificContextService.build_capability_matching_context(
            db=db,
            question_id=req.question_id,
            step_goal=req.step_goal,
            required_inputs=req.required_inputs,
            required_outputs=req.required_outputs,
            category=req.category,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/experiment-planning/inspect",
    response_model=ExperimentPlanningContext,
    summary="Inspect Experiment Planning Context",
)
def inspect_experiment_planning_context(
    req: ExperimentPlanningInspectRequest,
    db: DbSession,
):
    try:
        return ScientificContextService.build_experiment_planning_context(
            db=db,
            question_id=req.question_id,
            capability_key=req.capability_key,
            hypothesis_id=req.hypothesis_id,
            dataset_version_id=req.dataset_version_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/result-interpretation/inspect",
    response_model=ResultInterpretationContext,
    summary="Inspect Result Interpretation Context",
)
def inspect_result_interpretation_context(
    req: ResultInterpretationInspectRequest,
    db: DbSession,
):
    try:
        return ScientificContextService.build_result_interpretation_context(
            db=db,
            analysis_run_id=req.analysis_run_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
