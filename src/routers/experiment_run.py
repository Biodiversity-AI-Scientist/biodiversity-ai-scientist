from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.experiment_run import (
    ExperimentRunService,
    ExperimentRunNotFoundError,
    lifecycle,
    executor_service,
)
from src.schemas.experiment import (
    ExperimentRunCreate,
    ExperimentRunUpdate,
    ExperimentRunStartRequest,
    ExperimentRunCompleteRequest,
    ExperimentRunFailureRequest,
    ExperimentRunResponse,
    ExperimentExecutionResponse,
)
from src.schemas.result import ResultResponse

router = APIRouter(
    tags=["Experiment Runs"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/projects/{project_id}/experiment-runs",
    response_model=list[ExperimentRunResponse],
    summary="List Experiment Runs for a project",
    description="Retrieve all Experiment Runs executed within the specified research project.",
)
def list_project_experiment_runs(
    project_id: int,
    db: DbSession,
):
    try:
        return ExperimentRunService.list_experiment_runs_for_project(db, project_id)
    except (ExperimentRunNotFoundError, lifecycle.AnalysisPlanNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/experiments/{experiment_id}/runs",
    response_model=list[ExperimentRunResponse],
    summary="List Runs for an Experiment",
    description="Retrieve all execution runs associated with an Experiment.",
)
def list_experiment_runs(
    experiment_id: int,
    db: DbSession,
):
    try:
        return ExperimentRunService.list_experiment_runs_for_experiment(db, experiment_id)
    except (ExperimentRunNotFoundError, lifecycle.AnalysisPlanNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/experiments/{experiment_id}/runs",
    response_model=ExperimentRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an Experiment Run",
    description="Initialize a new Experiment Run in 'pending' status for the specified Experiment.",
)
def create_experiment_run(
    experiment_id: int,
    data: ExperimentRunCreate,
    db: DbSession,
):
    try:
        return ExperimentRunService.create_experiment_run(db, experiment_id, data)
    except lifecycle.AnalysisPlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except lifecycle.DatasetVersionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/experiment-runs/{run_id}",
    response_model=ExperimentRunResponse,
    summary="Get Experiment Run details",
    description="Retrieve execution details and status of an Experiment Run.",
)
def get_experiment_run(
    run_id: int,
    db: DbSession,
):
    try:
        return ExperimentRunService.get_experiment_run(db, run_id)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/experiment-runs/{run_id}",
    response_model=ExperimentRunResponse,
    summary="Update Experiment Run",
    description="Update metadata or parameters of an Experiment Run in non-terminal state.",
)
def update_experiment_run(
    run_id: int,
    data: ExperimentRunUpdate,
    db: DbSession,
):
    try:
        return ExperimentRunService.update_experiment_run(db, run_id, data)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except lifecycle.AnalysisRunConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/experiment-runs/{run_id}/start",
    response_model=ExperimentRunResponse,
    summary="Start Experiment Run",
    description="Transition Experiment Run state from 'pending' to 'running'.",
)
def start_experiment_run(
    run_id: int,
    db: DbSession,
    data: ExperimentRunStartRequest | None = None,
):
    try:
        return ExperimentRunService.start_experiment_run(db, run_id, data)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except lifecycle.InvalidAnalysisRunTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/experiment-runs/{run_id}/complete",
    response_model=ExperimentRunResponse,
    summary="Complete Experiment Run",
    description="Transition Experiment Run state from 'running' to 'completed'.",
)
def complete_experiment_run(
    run_id: int,
    db: DbSession,
    data: ExperimentRunCompleteRequest | None = None,
):
    try:
        return ExperimentRunService.complete_experiment_run(db, run_id, data)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except lifecycle.InvalidAnalysisRunTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/experiment-runs/{run_id}/fail",
    response_model=ExperimentRunResponse,
    summary="Fail Experiment Run",
    description="Mark an Experiment Run as 'failed' with error diagnostics.",
)
def fail_experiment_run(
    run_id: int,
    data: ExperimentRunFailureRequest,
    db: DbSession,
):
    try:
        return ExperimentRunService.fail_experiment_run(db, run_id, data)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except lifecycle.InvalidAnalysisRunTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/experiment-runs/{run_id}/execute",
    response_model=ExperimentExecutionResponse,
    summary="Execute Experiment Run",
    description="Orchestrates full execution of the experiment via its registered capability executor.",
)
def execute_experiment_run(
    run_id: int,
    db: DbSession,
):
    try:
        return ExperimentRunService.execute_experiment_run(db, run_id)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except executor_service.AnalysisExecutionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except executor_service.AnalysisExecutionValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except executor_service.AnalysisDatasetRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except executor_service.AnalysisExecutorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except executor_service.AnalysisExecutorFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/experiment-runs/{run_id}/results",
    response_model=list[ResultResponse],
    summary="List Results for Experiment Run",
    description="Retrieve all empirical Results produced by an Experiment Run.",
)
def list_experiment_run_results(
    run_id: int,
    db: DbSession,
):
    try:
        return ExperimentRunService.list_results_for_run(db, run_id)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
