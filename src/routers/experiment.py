from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.experiment import (
    ExperimentService,
    ExperimentNotFoundError,
    ExperimentValidationError,
)
from src.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentPlanAIRequest,
    ExperimentParameterOverrideRequest,
)

router = APIRouter(
    tags=["Experiments"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/projects/{project_id}/experiments",
    response_model=list[ExperimentResponse],
    summary="List Experiments for a project",
    description="Retrieve all Experiments registered within the specified research project.",
)
def list_project_experiments(
    project_id: int,
    db: DbSession,
):
    try:
        return ExperimentService.list_experiments_for_project(db, project_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/questions/{question_id}/experiments",
    response_model=list[ExperimentResponse],
    summary="List Experiments for a question",
    description="Retrieve all Experiments registered under a specific Research Question.",
)
def list_question_experiments(
    question_id: int,
    db: DbSession,
):
    try:
        return ExperimentService.list_experiments_for_question(db, question_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/questions/{question_id}/experiments",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Experiment",
    description="Register a new Experiment for a research question.",
)
def create_question_experiment(
    question_id: int,
    data: ExperimentCreate,
    db: DbSession,
):
    try:
        return ExperimentService.create_experiment(db, question_id, data)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/experiments/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Get Experiment details",
    description="Retrieve details and pre-specified parameters of a specific Experiment.",
)
def get_experiment(
    experiment_id: int,
    db: DbSession,
):
    try:
        return ExperimentService.get_experiment(db, experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/experiments/{experiment_id}",
    response_model=ExperimentResponse,
    summary="Update Experiment details",
    description="Update estimand, method, parameters, or status of an Experiment.",
)
def update_experiment(
    experiment_id: int,
    data: ExperimentUpdate,
    db: DbSession,
):
    try:
        return ExperimentService.update_experiment(db, experiment_id, data)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/experiments/{experiment_id}/approve",
    response_model=ExperimentResponse,
    summary="Approve Experiment",
    description="Approve and freeze an Experiment for execution (status: draft -> approved).",
)
def approve_experiment(
    experiment_id: int,
    db: DbSession,
):
    try:
        return ExperimentService.approve_experiment(db, experiment_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put(
    "/experiments/{experiment_id}/parameters",
    response_model=ExperimentResponse,
    summary="Override Experiment Parameters",
    description="Allow researcher to override pre-specified experiment parameters with recorded scientific justification.",
)
def override_experiment_parameters(
    experiment_id: int,
    req: ExperimentParameterOverrideRequest,
    db: DbSession,
):
    try:
        return ExperimentService.override_parameters(db, experiment_id, req)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/investigation-steps/{step_id}/experiments/plan",
    response_model=ExperimentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Plan Experiment for Investigation Step (LLM Stage 4)",
    description="Uses LLM Gateway Stage 4 reasoning to formulate a concrete Experiment from an investigation step and selected capability.",
)
def plan_experiment_for_step(
    step_id: int,
    db: DbSession,
    req: ExperimentPlanAIRequest | None = None,
):
    try:
        return ExperimentService.plan_experiment_for_step(
            db=db,
            step_id=step_id,
            user_guidance=req.user_guidance if req else None,
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/investigation-steps/{step_id}/experiments",
    response_model=list[ExperimentResponse],
    summary="List Experiments for Investigation Step",
    description="Retrieve all Experiments formulated for a specific Investigation Step.",
)
def list_step_experiments(
    step_id: int,
    db: DbSession,
):
    try:
        return ExperimentService.list_experiments_for_step(db, step_id)
    except ExperimentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
