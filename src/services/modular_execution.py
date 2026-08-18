"""
Modular Execution Service for BAIS.

Coordinates experiment execution through the generic boundary:
CapabilityAdapter -> ExecutionBackend -> ArtifactStore -> Result/Artifact persistence.
"""
from typing import Any
from sqlalchemy.orm import Session

from src.core.contracts.execution import JobState
from src.core.providers.registry import ProviderRegistry
from src.models import AnalysisPlan, AnalysisRun, Artifact, Result
from src.services import analysis_run as run_lifecycle


class ModularExecutionService:
    @classmethod
    def execute_modular_run(
        cls,
        db: Session,
        run_id: int,
        backend_name: str | None = None,
        artifact_store_name: str | None = None,
        dataset_store_name: str | None = None,
    ) -> tuple[AnalysisRun, list[Result], list[Artifact]]:
        registry = ProviderRegistry.get_instance()

        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            raise ValueError(f"AnalysisRun/ExperimentRun {run_id} not found")

        plan = db.query(AnalysisPlan).filter(AnalysisPlan.id == run.analysis_plan_id).first()
        if not plan:
            raise ValueError(f"Experiment {run.analysis_plan_id} not found for run {run_id}")

        capability_key = plan.method
        adapter = registry.get_adapter(capability_key)
        if not adapter:
            raise ValueError(f"No CapabilityAdapter registered for method/capability '{capability_key}'")

        backend = registry.get_backend(backend_name)
        artifact_store = registry.get_artifact_store(artifact_store_name)
        dataset_store = registry.get_dataset_store(dataset_store_name)

        from src.models import ResearchQuestion
        question = db.query(ResearchQuestion).filter(ResearchQuestion.id == plan.question_id).first()
        project_id = question.project_id if question else 1

        # 1. Mark run as running
        run = run_lifecycle.start_analysis_run(db, run_id)

        try:
            # 2. Prepare execution context
            params = run.parameters or plan.parameters or {}
            prepared_job = adapter.prepare_execution(
                experiment_id=plan.id,
                run_id=run.id,
                parameters=params,
                dataset_version_id=plan.dataset_version_id,
                dataset_store=dataset_store,
                artifact_store=artifact_store,
            )

            # 3. Dispatch to backend
            job_handle = backend.dispatch_job(
                command=prepared_job.command,
                working_dir=prepared_job.working_dir,
                env=prepared_job.env,
                resources=prepared_job.resources,
                job_metadata={
                    **prepared_job.job_metadata,
                    "project_id": project_id,
                },
            )

            # 4. Parse outcome
            outcome = adapter.parse_execution_output(
                experiment_id=plan.id,
                run_id=run.id,
                job_handle=job_handle,
                backend=backend,
                artifact_store=artifact_store,
            )

            if not outcome.success:
                run = run_lifecycle.fail_analysis_run(
                    db=db,
                    analysis_run_id=run_id,
                    error_type="CapabilityExecutionError",
                    error_message=outcome.error_message or outcome.summary,
                    error_details=outcome.diagnostics,
                )
                return run, [], []

            # 5. Persist Results & Artifacts
            result = Result(
                analysis_run_id=run.id,
                result_type=outcome.result_type,
                summary=outcome.summary,
                payload=outcome.metrics,
                diagnostics=outcome.diagnostics,
            )
            db.add(result)
            db.flush()

            persisted_artifacts = []
            for art_info in outcome.artifacts:
                art_record = Artifact(
                    project_id=project_id,
                    analysis_run_id=run.id,
                    artifact_type=art_info.artifact_type,
                    uri=art_info.uri,
                    size_bytes=art_info.size_bytes,
                    sha256=art_info.sha256,
                )
                db.add(art_record)
                persisted_artifacts.append(art_record)

            db.commit()
            db.refresh(run)
            db.refresh(result)

            # 6. Mark run complete
            run = run_lifecycle.complete_analysis_run(
                db=db,
                analysis_run_id=run_id,
                execution_metadata={
                    "backend": backend.backend_name,
                    "artifact_store": artifact_store.store_name,
                    "adapter": adapter.capability_key,
                    "metrics": outcome.metrics,
                },
            )

            return run, [result], persisted_artifacts

        except Exception as ex:
            run = run_lifecycle.fail_analysis_run(
                db=db,
                analysis_run_id=run_id,
                error_type=type(ex).__name__,
                error_message=str(ex),
            )
            raise
