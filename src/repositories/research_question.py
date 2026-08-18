from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import ResearchProject, ResearchQuestion
from src.schemas.research_question import ResearchQuestionCreate


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


def get_questions_for_project(
    db: Session,
    project_id: int,
) -> list[ResearchQuestion]:

    statement = (
        select(ResearchQuestion)
        .where(
            ResearchQuestion.project_id == project_id
        )
        .order_by(
            ResearchQuestion.id
        )
    )

    return list(
        db.scalars(statement).all()
    )


def create_question(
    db: Session,
    project_id: int,
    question_data: ResearchQuestionCreate,
) -> ResearchQuestion:

    question = ResearchQuestion(
        project_id=project_id,
        parent_question_id=question_data.parent_question_id,
        question=question_data.question,
        inferential_level=question_data.inferential_level,
        source=question_data.source or "user",
        brainstorming_session_id=question_data.brainstorming_session_id,
        status="open",
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


def update_question(
    db: Session,
    question: ResearchQuestion,
    question_data: "ResearchQuestionUpdate",
) -> ResearchQuestion:
    changes = question_data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


def delete_question(
    db: Session,
    question: ResearchQuestion,
) -> None:
    db.delete(question)
    db.commit()

