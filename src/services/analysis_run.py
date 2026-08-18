"""
AnalysisRun (Experiment Run) Lifecycle Service.

Internal/legacy identifier AnalysisRun is retained for backend, database, and API compatibility.
Scientifically, this service orchestrates the lifecycle transitions of an **Experiment Run**
(one execution instance of an Experiment / AnalysisPlan).
"""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session


from src.models import AnalysisRun
from src.repositories import analysis_run as repository
from src.schemas.analysis_run import AnalysisRunCreate, AnalysisRunUpdate


class AnalysisRunServiceError(Exception):
    """Base exception for expected analysis-run service failures."""



class AnalysisPlanNotFoundError(AnalysisRunServiceError):
    pass


class AnalysisRunNotFoundError(AnalysisRunServiceError):
    pass


class AnalysisRunConflictError(AnalysisRunServiceError):
    pass


class DatasetVersionNotFoundError(AnalysisRunServiceError):
    pass


class InvalidAnalysisRunTransitionError(AnalysisRunServiceError):
    pass


VALID_TRANSITIONS = {
    "pending": {"running"},
    "running": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _commit(db: Session, run: AnalysisRun) -> AnalysisRun:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(run)
    return run


def get_analysis_run(db: Session, analysis_run_id: int) -> AnalysisRun:
    run = repository.get_analysis_run(db, analysis_run_id)
    if run is None:
        raise AnalysisRunNotFoundError("Analysis run not found")
    return run


def list_analysis_runs_for_plan(
    db: Session,
    analysis_plan_id: int,
) -> list[AnalysisRun]:
    if repository.get_analysis_plan(db, analysis_plan_id) is None:
        raise AnalysisPlanNotFoundError("Analysis plan not found")
    return repository.get_runs_for_plan(db, analysis_plan_id)


def list_analysis_runs_for_project(
    db: Session,
    project_id: int,
) -> list[AnalysisRun]:
    if repository.get_project(db, project_id) is None:
        raise AnalysisPlanNotFoundError("Research project not found")
    return repository.get_runs_for_project(db, project_id)


def create_analysis_run(
    db: Session,
    analysis_plan_id: int,
    run_data: AnalysisRunCreate,
) -> AnalysisRun:
    plan = repository.get_analysis_plan(db, analysis_plan_id)
    if plan is None:
        raise AnalysisPlanNotFoundError("Analysis plan not found")

    question = repository.get_question(db, plan.question_id)
    if question is None:
        raise AnalysisRunConflictError(
            "Analysis plan references a missing research question"
        )

    requested_dataset_id = run_data.dataset_version_id
    if plan.dataset_version_id is not None:
        if requested_dataset_id not in {None, plan.dataset_version_id}:
            raise AnalysisRunConflictError(
                "Analysis run dataset does not match the DatasetVersion "
                "specified by the AnalysisPlan"
            )
        dataset_version_id = plan.dataset_version_id
    else:
        dataset_version_id = requested_dataset_id

    # Actual parameters default to plan proposed parameters if not explicitly overridden
    effective_parameters = (
        run_data.parameters if run_data.parameters is not None else plan.parameters
    )

    if dataset_version_id is not None:
        dataset = repository.get_dataset_version(db, dataset_version_id)
        if dataset is None:
            raise DatasetVersionNotFoundError("Dataset version not found")
        if dataset.project_id != question.project_id:
            raise AnalysisRunConflictError(
                "Dataset version does not belong to the same research project"
            )

    try:
        run = repository.create_analysis_run(
            db=db,
            analysis_plan_id=analysis_plan_id,
            dataset_version_id=dataset_version_id,
            run_data=run_data.model_copy(
                update={"parameters": effective_parameters}
            ),
        )
        return _commit(db, run)
    except Exception:
        db.rollback()
        raise


def update_analysis_run_metadata(
    db: Session,
    analysis_run_id: int,
    update_data: AnalysisRunUpdate,
) -> AnalysisRun:
    run = get_analysis_run(db, analysis_run_id)
    if run.status != "pending":
        raise AnalysisRunConflictError(
            "Analysis run metadata can only be changed while pending"
        )
    repository.apply_analysis_run_updates(db, run, update_data)
    return _commit(db, run)


def _transition(
    db: Session,
    run: AnalysisRun,
    new_status: str,
    error_message: str | None = None,
    error_type: str | None = None,
    error_details: dict[str, Any] | list[Any] | str | None = None,
    execution_metadata: dict[str, Any] | None = None,
    parameters: dict[str, Any] | None = None,
) -> AnalysisRun:
    allowed = VALID_TRANSITIONS.get(run.status, set())
    if new_status not in allowed:
        raise InvalidAnalysisRunTransitionError(
            f"Analysis run cannot transition from {run.status} to {new_status}"
        )

    now = _now()
    run.status = new_status

    if new_status == "running":
        run.started_at = now
        run.completed_at = None
        run.error_message = None
        run.error_type = None
        run.error_details = None
        if parameters:
            run.parameters = {**(run.parameters or {}), **parameters}
        if execution_metadata:
            run.execution_metadata = {**(run.execution_metadata or {}), **execution_metadata}
    elif new_status == "completed":
        run.completed_at = now
        run.error_message = None
        run.error_type = None
        run.error_details = None
        if execution_metadata:
            run.execution_metadata = {**(run.execution_metadata or {}), **execution_metadata}
    else:  # failed
        run.completed_at = now
        failure_detail = (error_message or "").strip()
        run.error_message = failure_detail or "Analysis execution failed"
        run.error_type = error_type or "ExecutionError"
        run.error_details = error_details
        if execution_metadata:
            run.execution_metadata = {**(run.execution_metadata or {}), **execution_metadata}

    return _commit(db, run)


def start_analysis_run(
    db: Session,
    analysis_run_id: int,
    parameters: dict[str, Any] | None = None,
    execution_metadata: dict[str, Any] | None = None,
) -> AnalysisRun:
    return _transition(
        db,
        get_analysis_run(db, analysis_run_id),
        "running",
        parameters=parameters,
        execution_metadata=execution_metadata,
    )


def complete_analysis_run(
    db: Session,
    analysis_run_id: int,
    execution_metadata: dict[str, Any] | None = None,
) -> AnalysisRun:
    return _transition(
        db,
        get_analysis_run(db, analysis_run_id),
        "completed",
        execution_metadata=execution_metadata,
    )


def fail_analysis_run(
    db: Session,
    analysis_run_id: int,
    error_message: str,
    error_type: str | None = None,
    error_details: dict[str, Any] | list[Any] | str | None = None,
    execution_metadata: dict[str, Any] | None = None,
) -> AnalysisRun:
    return _transition(
        db,
        get_analysis_run(db, analysis_run_id),
        "failed",
        error_message=error_message,
        error_type=error_type,
        error_details=error_details,
        execution_metadata=execution_metadata,
    )

