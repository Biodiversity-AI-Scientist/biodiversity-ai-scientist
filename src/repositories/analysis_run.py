from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    AnalysisPlan,
    AnalysisRun,
    DatasetVersion,
    ResearchProject,
    ResearchQuestion,
    Result,
)
from src.schemas.analysis_run import (
    AnalysisRunCreate,
    AnalysisRunUpdate,
)


def get_project(
    db: Session,
    project_id: int,
) -> ResearchProject | None:
    return db.get(ResearchProject, project_id)


def get_analysis_plan(
    db: Session,
    analysis_plan_id: int,
) -> AnalysisPlan | None:
    return db.get(
        AnalysisPlan,
        analysis_plan_id,
    )


def get_analysis_run(
    db: Session,
    analysis_run_id: int,
) -> AnalysisRun | None:
    return db.get(
        AnalysisRun,
        analysis_run_id,
    )


def get_analysis_run_for_update(
    db: Session,
    analysis_run_id: int,
) -> AnalysisRun | None:
    statement = (
        select(AnalysisRun)
        .where(AnalysisRun.id == analysis_run_id)
        .with_for_update()
    )
    return db.scalar(statement)


def get_dataset_version(
    db: Session,
    dataset_version_id: int,
) -> DatasetVersion | None:
    return db.get(
        DatasetVersion,
        dataset_version_id,
    )


def get_question(
    db: Session,
    question_id: int,
) -> ResearchQuestion | None:
    return db.get(
        ResearchQuestion,
        question_id,
    )


def get_runs_for_plan(
    db: Session,
    analysis_plan_id: int,
) -> list[AnalysisRun]:

    statement = (
        select(AnalysisRun)
        .where(
            AnalysisRun.analysis_plan_id
            == analysis_plan_id
        )
        .order_by(
            AnalysisRun.created_at.desc(),
            AnalysisRun.id.desc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_runs_for_project(
    db: Session,
    project_id: int,
) -> list[AnalysisRun]:

    statement = (
        select(AnalysisRun)
        .join(
            AnalysisPlan,
            AnalysisRun.analysis_plan_id
            == AnalysisPlan.id,
        )
        .join(
            ResearchQuestion,
            AnalysisPlan.question_id
            == ResearchQuestion.id,
        )
        .where(
            ResearchQuestion.project_id
            == project_id
        )
        .order_by(
            AnalysisRun.created_at.desc(),
            AnalysisRun.id.desc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_results_for_run(
    db: Session,
    analysis_run_id: int,
) -> list[Result]:
    statement = (
        select(Result)
        .where(Result.analysis_run_id == analysis_run_id)
        .order_by(Result.id)
    )
    return list(db.scalars(statement).all())


def create_analysis_run(
    db: Session,
    analysis_plan_id: int,
    dataset_version_id: int | None,
    run_data: AnalysisRunCreate,
) -> AnalysisRun:

    run = AnalysisRun(
        analysis_plan_id=analysis_plan_id,
        dataset_version_id=dataset_version_id,
        status="pending",
        tool_name=run_data.tool_name,
        tool_version=run_data.tool_version,
        source_code_commit=run_data.source_code_commit,
        generated_code_hash=run_data.generated_code_hash,
        container_image_digest=run_data.container_image_digest,
        model_version=run_data.model_version,
        parameters=run_data.parameters,
        random_seeds=run_data.random_seeds,
        hardware_metadata=run_data.hardware_metadata,
        execution_metadata=run_data.execution_metadata,
        error_type=None,
        error_message=None,
        error_details=None,
        started_at=None,
        completed_at=None,
    )

    db.add(run)
    db.flush()

    return run



def apply_analysis_run_updates(
    db: Session,
    run: AnalysisRun,
    update_data: AnalysisRunUpdate,
) -> AnalysisRun:

    changes = update_data.model_dump(
        exclude_unset=True,
    )

    for field, value in changes.items():
        setattr(
            run,
            field,
            value,
        )

    return run
