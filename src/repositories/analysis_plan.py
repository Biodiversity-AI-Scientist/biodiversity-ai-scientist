from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    AnalysisPlan,
    DatasetVersion,
    Hypothesis,
    ResearchProject,
    ResearchQuestion,
)
from src.schemas.analysis_plan import AnalysisPlanCreate


def get_project(
    db: Session,
    project_id: int,
) -> ResearchProject | None:
    return db.get(
        ResearchProject,
        project_id,
    )


def get_question(
    db: Session,
    question_id: int,
) -> ResearchQuestion | None:
    return db.get(
        ResearchQuestion,
        question_id,
    )


def get_hypothesis(
    db: Session,
    hypothesis_id: int,
) -> Hypothesis | None:
    return db.get(
        Hypothesis,
        hypothesis_id,
    )


def get_dataset_version(
    db: Session,
    dataset_version_id: int,
) -> DatasetVersion | None:
    return db.get(
        DatasetVersion,
        dataset_version_id,
    )


def get_analysis_plan(
    db: Session,
    analysis_plan_id: int,
) -> AnalysisPlan | None:
    return db.get(
        AnalysisPlan,
        analysis_plan_id,
    )


def get_plans_for_question(
    db: Session,
    question_id: int,
) -> list[AnalysisPlan]:

    statement = (
        select(AnalysisPlan)
        .where(
            AnalysisPlan.question_id == question_id
        )
        .order_by(
            AnalysisPlan.created_at.desc(),
            AnalysisPlan.id.desc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_plans_for_project(
    db: Session,
    project_id: int,
) -> list[AnalysisPlan]:

    statement = (
        select(AnalysisPlan)
        .join(
            ResearchQuestion,
            AnalysisPlan.question_id == ResearchQuestion.id,
        )
        .where(
            ResearchQuestion.project_id == project_id
        )
        .order_by(
            AnalysisPlan.created_at.desc(),
            AnalysisPlan.id.desc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def create_analysis_plan(
    db: Session,
    question_id: int,
    plan_data: AnalysisPlanCreate,
) -> AnalysisPlan:

    plan = AnalysisPlan(
        question_id=question_id,
        hypothesis_id=plan_data.hypothesis_id,
        dataset_version_id=plan_data.dataset_version_id,
        estimand=plan_data.estimand,
        method=plan_data.method,
        assumptions=plan_data.assumptions,
        parameters=plan_data.parameters,
        exploratory=plan_data.exploratory,
        status="proposed",
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan
