"""
DEPRECATED: Legacy AnalysisPlan router.

Maintained exclusively as backward-compatible shims for legacy callers.
Delegates all business logic to canonical ExperimentService in src.services.experiment.
All calls trigger structured deprecation telemetry.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.experiment import (
    ExperimentService,
    ExperimentNotFoundError,
    ExperimentValidationError,
)
from src.schemas.experiment import (
    AnalysisPlanCreate,
    AnalysisPlanResponse,
    ExperimentUpdate,
    ExperimentPlanAIRequest,
    ExperimentParameterOverrideRequest,
)
from src.telemetry.deprecation import log_legacy_api_access

router = APIRouter(
    tags=["Legacy Analysis Plans (Deprecated - Use Experiments)"],
    deprecated=True,
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/projects/{project_id}/analysis-plans",
    response_model=list[AnalysisPlanResponse],
    summary="[DEPRECATED] List Analysis Plans for a project",
    description="DEPRECATED: Use GET /projects/{project_id}/experiments instead. Retrieves all experiments for a project.",
    deprecated=True,
)
def list_project_analysis_plans(
    project_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/projects/{project_id}/analysis-plans",
        canonical_endpoint="/projects/{project_id}/experiments",
    )
    try:
        return ExperimentService.list_experiments_for_project(db, project_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/questions/{question_id}/analysis-plans",
    response_model=list[AnalysisPlanResponse],
    summary="[DEPRECATED] List Analysis Plans for a question",
    description="DEPRECATED: Use GET /questions/{question_id}/experiments instead.",
    deprecated=True,
)
def list_question_analysis_plans(
    question_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/questions/{question_id}/analysis-plans",
        canonical_endpoint="/questions/{question_id}/experiments",
    )
    try:
        return ExperimentService.list_experiments_for_question(db, question_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/questions/{question_id}/analysis-plans",
    response_model=AnalysisPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[DEPRECATED] Create an Analysis Plan",
    description="DEPRECATED: Use POST /questions/{question_id}/experiments instead.",
    deprecated=True,
)
def create_question_analysis_plan(
    question_id: int,
    data: AnalysisPlanCreate,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/questions/{question_id}/analysis-plans",
        canonical_endpoint="/questions/{question_id}/experiments",
    )
    try:
        return ExperimentService.create_experiment(db, question_id, data)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/analysis-plans/{analysis_plan_id}",
    response_model=AnalysisPlanResponse,
    summary="[DEPRECATED] Get Analysis Plan details",
    description="DEPRECATED: Use GET /experiments/{experiment_id} instead.",
    deprecated=True,
)
def get_analysis_plan(
    analysis_plan_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-plans/{analysis_plan_id}",
        canonical_endpoint="/experiments/{experiment_id}",
    )
    try:
        return ExperimentService.get_experiment(db, analysis_plan_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/analysis-plans/{analysis_plan_id}/approve",
    response_model=AnalysisPlanResponse,
    summary="[DEPRECATED] Approve Analysis Plan",
    description="DEPRECATED: Use POST /experiments/{experiment_id}/approve instead.",
    deprecated=True,
)
def approve_analysis_plan(
    analysis_plan_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-plans/{analysis_plan_id}/approve",
        canonical_endpoint="/experiments/{experiment_id}/approve",
    )
    try:
        return ExperimentService.approve_experiment(db, analysis_plan_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/analysis-plans/{analysis_plan_id}/parameters",
    response_model=AnalysisPlanResponse,
    summary="[DEPRECATED] Override Analysis Plan Parameters",
    description="DEPRECATED: Use PUT /experiments/{experiment_id}/parameters instead.",
    deprecated=True,
)
def override_analysis_plan_parameters(
    analysis_plan_id: int,
    req: ExperimentParameterOverrideRequest,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-plans/{analysis_plan_id}/parameters",
        canonical_endpoint="/experiments/{experiment_id}/parameters",
    )
    try:
        return ExperimentService.override_parameters(db, analysis_plan_id, req)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
