"""
DEPRECATED: Legacy AnalysisRun router.

Maintained exclusively as backward-compatible shims for legacy callers.
Delegates all business logic to canonical ExperimentRunService in src.services.experiment_run.
All calls trigger structured deprecation telemetry.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.experiment_run import (
    ExperimentRunService,
    lifecycle,
    executor_service,
)
from src.schemas.experiment import (
    AnalysisRunCreate,
    AnalysisRunUpdate,
    AnalysisRunStartRequest,
    AnalysisRunCompleteRequest,
    AnalysisRunFailureRequest,
    AnalysisRunResponse,
    ExperimentExecutionResponse as AnalysisExecutionResponse,
)
from src.schemas.result import ResultResponse
from src.telemetry.deprecation import log_legacy_api_access

router = APIRouter(
    tags=["Legacy Analysis Runs (Deprecated - Use Experiment Runs)"],
    deprecated=True,
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/projects/{project_id}/analysis-runs",
    response_model=list[AnalysisRunResponse],
    summary="[DEPRECATED] List Analysis Runs for a project",
    description="DEPRECATED: Use GET /projects/{project_id}/experiment-runs instead.",
    deprecated=True,
)
def list_project_analysis_runs(
    project_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/projects/{project_id}/analysis-runs",
        canonical_endpoint="/projects/{project_id}/experiment-runs",
    )
    try:
        return ExperimentRunService.list_experiment_runs_for_project(db, project_id)
    except lifecycle.AnalysisPlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/analysis-plans/{analysis_plan_id}/runs",
    response_model=list[AnalysisRunResponse],
    summary="[DEPRECATED] List Runs for an Analysis Plan",
    description="DEPRECATED: Use GET /experiments/{experiment_id}/runs instead.",
    deprecated=True,
)
def list_analysis_plan_runs(
    analysis_plan_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-plans/{analysis_plan_id}/runs",
        canonical_endpoint="/experiments/{experiment_id}/runs",
    )
    try:
        return ExperimentRunService.list_experiment_runs_for_experiment(db, analysis_plan_id)
    except lifecycle.AnalysisPlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/analysis-plans/{analysis_plan_id}/runs",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[DEPRECATED] Create an Analysis Run",
    description="DEPRECATED: Use POST /experiments/{experiment_id}/runs instead.",
    deprecated=True,
)
def create_analysis_plan_run(
    analysis_plan_id: int,
    run_data: AnalysisRunCreate,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-plans/{analysis_plan_id}/runs",
        canonical_endpoint="/experiments/{experiment_id}/runs",
    )
    try:
        return ExperimentRunService.create_experiment_run(
            db=db,
            experiment_id=analysis_plan_id,
            run_data=run_data,
        )
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
    "/analysis-runs/{analysis_run_id}",
    response_model=AnalysisRunResponse,
    summary="[DEPRECATED] Get Analysis Run details",
    description="DEPRECATED: Use GET /experiment-runs/{run_id} instead.",
    deprecated=True,
)
def get_analysis_run(
    analysis_run_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}",
        canonical_endpoint="/experiment-runs/{run_id}",
    )
    try:
        return ExperimentRunService.get_experiment_run(db, analysis_run_id)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/analysis-runs/{analysis_run_id}",
    response_model=AnalysisRunResponse,
    summary="[DEPRECATED] Update Analysis Run",
    description="DEPRECATED: Use PATCH /experiment-runs/{run_id} instead.",
    deprecated=True,
)
def update_analysis_run(
    analysis_run_id: int,
    update_data: AnalysisRunUpdate,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}",
        canonical_endpoint="/experiment-runs/{run_id}",
    )
    try:
        return ExperimentRunService.update_experiment_run(
            db=db,
            run_id=analysis_run_id,
            update_data=update_data,
        )
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
    "/analysis-runs/{analysis_run_id}/start",
    response_model=AnalysisRunResponse,
    summary="[DEPRECATED] Start Analysis Run",
    description="DEPRECATED: Use POST /experiment-runs/{run_id}/start instead.",
    deprecated=True,
)
def start_analysis_run(
    analysis_run_id: int,
    request: Request,
    db: DbSession,
    start_data: AnalysisRunStartRequest | None = None,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}/start",
        canonical_endpoint="/experiment-runs/{run_id}/start",
    )
    try:
        return ExperimentRunService.start_experiment_run(
            db=db,
            run_id=analysis_run_id,
            req=start_data,
        )
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
    "/analysis-runs/{analysis_run_id}/complete",
    response_model=AnalysisRunResponse,
    summary="[DEPRECATED] Complete Analysis Run",
    description="DEPRECATED: Use POST /experiment-runs/{run_id}/complete instead.",
    deprecated=True,
)
def complete_analysis_run(
    analysis_run_id: int,
    request: Request,
    db: DbSession,
    complete_data: AnalysisRunCompleteRequest | None = None,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}/complete",
        canonical_endpoint="/experiment-runs/{run_id}/complete",
    )
    try:
        return ExperimentRunService.complete_experiment_run(
            db=db,
            run_id=analysis_run_id,
            req=complete_data,
        )
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
    "/analysis-runs/{analysis_run_id}/fail",
    response_model=AnalysisRunResponse,
    summary="[DEPRECATED] Fail Analysis Run",
    description="DEPRECATED: Use POST /experiment-runs/{run_id}/fail instead.",
    deprecated=True,
)
def fail_analysis_run(
    analysis_run_id: int,
    failure_data: AnalysisRunFailureRequest,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}/fail",
        canonical_endpoint="/experiment-runs/{run_id}/fail",
    )
    try:
        return ExperimentRunService.fail_experiment_run(
            db=db,
            run_id=analysis_run_id,
            req=failure_data,
        )
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
    "/analysis-runs/{analysis_run_id}/execute",
    response_model=AnalysisExecutionResponse,
    summary="[DEPRECATED] Execute Analysis Run",
    description="DEPRECATED: Use POST /experiment-runs/{run_id}/execute instead.",
    deprecated=True,
)
def execute_analysis_run(
    analysis_run_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}/execute",
        canonical_endpoint="/experiment-runs/{run_id}/execute",
    )
    try:
        return ExperimentRunService.execute_experiment_run(db, analysis_run_id)
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
    "/analysis-runs/{analysis_run_id}/results",
    response_model=list[ResultResponse],
    summary="[DEPRECATED] List Results for Analysis Run",
    description="DEPRECATED: Use GET /experiment-runs/{run_id}/results instead.",
    deprecated=True,
)
def list_analysis_run_results(
    analysis_run_id: int,
    request: Request,
    db: DbSession,
):
    log_legacy_api_access(
        request=request,
        legacy_endpoint="/analysis-runs/{analysis_run_id}/results",
        canonical_endpoint="/experiment-runs/{run_id}/results",
    )
    try:
        return ExperimentRunService.list_results_for_run(db, analysis_run_id)
    except lifecycle.AnalysisRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
