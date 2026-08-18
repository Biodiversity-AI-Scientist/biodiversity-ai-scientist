"""
Canonical ExperimentRun Domain Service.

Manages execution instances, lifecycle state transitions, and executor orchestration
for Experiment Runs (internally stored in the analysis_run table).
"""
import logging
from sqlalchemy.orm import Session

from src.models import AnalysisRun, Result
from src.repositories import analysis_run as repository
from src.services import analysis_run as lifecycle
from src.services import analysis_execution as executor_service
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

logger = logging.getLogger(__name__)


class ExperimentRunServiceError(Exception):
    """Base exception for ExperimentRun service."""


class ExperimentRunNotFoundError(ExperimentRunServiceError):
    pass


class ExperimentRunService:
    @classmethod
    def list_experiment_runs_for_project(
        cls,
        db: Session,
        project_id: int,
    ) -> list[ExperimentRunResponse]:
        runs = lifecycle.list_analysis_runs_for_project(db, project_id)
        return [ExperimentRunResponse.model_validate(r) for r in runs]

    @classmethod
    def list_experiment_runs_for_experiment(
        cls,
        db: Session,
        experiment_id: int,
    ) -> list[ExperimentRunResponse]:
        runs = lifecycle.list_analysis_runs_for_plan(db, experiment_id)
        return [ExperimentRunResponse.model_validate(r) for r in runs]

    @classmethod
    def get_experiment_run(
        cls,
        db: Session,
        run_id: int,
    ) -> ExperimentRunResponse:
        run = lifecycle.get_analysis_run(db, run_id)
        return ExperimentRunResponse.model_validate(run)

    @classmethod
    def create_experiment_run(
        cls,
        db: Session,
        experiment_id: int,
        run_data: ExperimentRunCreate,
    ) -> ExperimentRunResponse:
        run = lifecycle.create_analysis_run(
            db=db,
            analysis_plan_id=experiment_id,
            run_data=run_data,
        )
        return ExperimentRunResponse.model_validate(run)

    @classmethod
    def update_experiment_run(
        cls,
        db: Session,
        run_id: int,
        update_data: ExperimentRunUpdate,
    ) -> ExperimentRunResponse:
        run = lifecycle.update_analysis_run_metadata(
            db=db,
            analysis_run_id=run_id,
            update_data=update_data,
        )
        return ExperimentRunResponse.model_validate(run)

    @classmethod
    def start_experiment_run(
        cls,
        db: Session,
        run_id: int,
        req: ExperimentRunStartRequest | None = None,
    ) -> ExperimentRunResponse:
        params = req.parameters if req else None
        exec_meta = req.execution_metadata if req else None
        run = lifecycle.start_analysis_run(
            db=db,
            analysis_run_id=run_id,
            parameters=params,
            execution_metadata=exec_meta,
        )
        return ExperimentRunResponse.model_validate(run)

    @classmethod
    def complete_experiment_run(
        cls,
        db: Session,
        run_id: int,
        req: ExperimentRunCompleteRequest | None = None,
    ) -> ExperimentRunResponse:
        exec_meta = req.execution_metadata if req else None
        run = lifecycle.complete_analysis_run(
            db=db,
            analysis_run_id=run_id,
            execution_metadata=exec_meta,
        )
        return ExperimentRunResponse.model_validate(run)

    @classmethod
    def fail_experiment_run(
        cls,
        db: Session,
        run_id: int,
        req: ExperimentRunFailureRequest,
    ) -> ExperimentRunResponse:
        run = lifecycle.fail_analysis_run(
            db=db,
            analysis_run_id=run_id,
            error_message=req.error_message or req.reason or "Experiment run failed",
            error_type=req.error_type,
            error_details=req.error_details,
        )
        return ExperimentRunResponse.model_validate(run)

    @classmethod
    def execute_experiment_run(
        cls,
        db: Session,
        run_id: int,
    ) -> ExperimentExecutionResponse:
        run, results = executor_service.execute_analysis_run(db, run_id)
        return ExperimentExecutionResponse(
            run=ExperimentRunResponse.model_validate(run),
            results=[ResultResponse.model_validate(r) for r in results],
        )

    @classmethod
    def list_results_for_run(
        cls,
        db: Session,
        run_id: int,
    ) -> list[ResultResponse]:
        results = executor_service.list_results_for_run(db, run_id)
        return [ResultResponse.model_validate(r) for r in results]
