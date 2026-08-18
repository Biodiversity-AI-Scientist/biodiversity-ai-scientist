from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import (
    Hypothesis,
    ResearchProject,
    ResearchQuestion,
)
from src.schemas.hypothesis import HypothesisCreate


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


def get_hypotheses_for_project(
    db: Session,
    project_id: int,
) -> list[Hypothesis]:

    statement = (
        select(Hypothesis)
        .join(
            ResearchQuestion,
            Hypothesis.question_id == ResearchQuestion.id,
        )
        .where(
            ResearchQuestion.project_id == project_id
        )
        .order_by(
            Hypothesis.id
        )
    )

    return list(
        db.scalars(statement).all()
    )


def get_hypotheses_for_question(
    db: Session,
    question_id: int,
) -> list[Hypothesis]:

    statement = (
        select(Hypothesis)
        .where(
            Hypothesis.question_id == question_id
        )
        .order_by(
            Hypothesis.id
        )
    )

    return list(
        db.scalars(statement).all()
    )


def create_hypothesis(
    db: Session,
    question_id: int,
    hypothesis_data: HypothesisCreate,
) -> Hypothesis:

    hypothesis = Hypothesis(
        question_id=question_id,
        statement=hypothesis_data.statement,
        rationale=hypothesis_data.rationale,
        source=hypothesis_data.source or "user",
        brainstorming_session_id=hypothesis_data.brainstorming_session_id,
        status="proposed",
    )

    db.add(hypothesis)
    db.commit()
    db.refresh(hypothesis)

    return hypothesis


def update_hypothesis(
    db: Session,
    hypothesis: Hypothesis,
    hypothesis_data: "HypothesisUpdate",
) -> Hypothesis:
    changes = hypothesis_data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(hypothesis, field, value)
    db.commit()
    db.refresh(hypothesis)
    return hypothesis


def delete_hypothesis(
    db: Session,
    hypothesis: Hypothesis,
) -> None:
    db.delete(hypothesis)
    db.commit()

