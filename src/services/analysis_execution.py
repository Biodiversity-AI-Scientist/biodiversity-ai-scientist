from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.executors.base import (
    AnalysisComputationError,
    AnalysisExecutionContext,
)
from src.executors.registry import (
    UnknownAnalysisTypeError,
    get_executor,
)
from src.models import AnalysisRun, Result
from src.repositories import analysis_run as repository
from src.services import analysis_run as lifecycle


class AnalysisExecutionError(Exception):
    """Base exception for expected execution-orchestration failures."""


class AnalysisExecutionConflictError(AnalysisExecutionError):
    pass


class AnalysisExecutionValidationError(AnalysisExecutionError):
    pass


class AnalysisExecutorNotFoundError(AnalysisExecutionError):
    pass


class AnalysisDatasetRequiredError(AnalysisExecutionError):
    pass


class AnalysisExecutorFailedError(AnalysisExecutionError):
    pass


def _sanitize_execution_error(exc: Exception) -> str:
    if isinstance(exc, AnalysisComputationError):
        message = str(exc).strip()
        if message:
            return message[:2000]
    return (
        "Registered analysis executor failed "
        f"with {type(exc).__name__}"
    )


def list_results_for_run(
    db: Session,
    analysis_run_id: int,
) -> list[Result]:
    lifecycle.get_analysis_run(db, analysis_run_id)
    return repository.get_results_for_run(db, analysis_run_id)


def execute_analysis_run(
    db: Session,
    analysis_run_id: int,
) -> tuple[AnalysisRun, list[Result]]:
    run = repository.get_analysis_run_for_update(
        db,
        analysis_run_id,
    )
    if run is None:
        raise lifecycle.AnalysisRunNotFoundError(
            "Analysis run not found"
        )
    if run.status != "pending":
        db.rollback()
        raise AnalysisExecutionConflictError(
            f"Analysis run in status '{run.status}' cannot be executed"
        )

    plan = repository.get_analysis_plan(db, run.analysis_plan_id)
    if plan is None:
        db.rollback()
        raise AnalysisExecutionConflictError(
            "Analysis run references a missing AnalysisPlan"
        )
    if run.dataset_version_id is None:
        db.rollback()
        raise AnalysisDatasetRequiredError(
            "Analysis run requires an explicit DatasetVersion"
        )

    dataset = repository.get_dataset_version(
        db,
        run.dataset_version_id,
    )
    if dataset is None:
        db.rollback()
        raise AnalysisDatasetRequiredError(
            "Analysis run references a missing DatasetVersion"
        )
    if (
        plan.dataset_version_id is not None
        and plan.dataset_version_id != run.dataset_version_id
    ):
        db.rollback()
        raise AnalysisExecutionConflictError(
            "AnalysisRun DatasetVersion no longer matches its AnalysisPlan"
        )

    try:
        executor = get_executor(plan.method)
    except UnknownAnalysisTypeError as exc:
        from src.core.providers.registry import ProviderRegistry
        from src.services.modular_execution import ModularExecutionService
        if ProviderRegistry.get_instance().get_adapter(plan.method):
            run, results, _ = ModularExecutionService.execute_modular_run(db, run.id)
            return run, results
        db.rollback()
        raise AnalysisExecutorNotFoundError(str(exc)) from exc

    raw_parameters = run.parameters or {}
    try:
        validated_parameters = executor.parameter_schema.model_validate(
            raw_parameters
        )
    except ValidationError as exc:
        db.rollback()
        raise AnalysisExecutionValidationError(
            "Analysis parameters are invalid for the registered executor: "
            f"{exc.errors(include_url=False)}"
        ) from exc

    run.tool_name = executor.analysis_type
    run.tool_version = executor.version
    run.parameters = validated_parameters.model_dump(mode="json")
    lifecycle.start_analysis_run(db, run.id)

    context = AnalysisExecutionContext(
        analysis_run=run,
        analysis_plan=plan,
        dataset_version=dataset,
        parameters=validated_parameters,
    )

    try:
        output = executor.execute(context)
        if not output.results:
            raise RuntimeError(
                "Registered executor returned no analytical results"
            )

        results = [
            Result(
                analysis_run_id=run.id,
                result_type=item.result_type,
                summary=item.summary,
                payload=item.payload,
                uncertainty=item.uncertainty,
                diagnostics=item.diagnostics,
            )
            for item in output.results
        ]
        db.add_all(results)
        lifecycle.complete_analysis_run(db, run.id)
        for result in results:
            db.refresh(result)
        return run, results
    except Exception as exc:
        db.rollback()
        try:
            lifecycle.fail_analysis_run(
                db,
                run.id,
                _sanitize_execution_error(exc),
            )
        except Exception:
            db.rollback()
            raise
        raise AnalysisExecutorFailedError(
            "Registered analysis execution failed"
        ) from exc
