from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import research_question as repository
from src.schemas.research_question import (
    ResearchQuestionCreate,
    ResearchQuestionResponse,
    ResearchQuestionUpdate,
)



router = APIRouter(
    tags=["Research questions"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/projects/{project_id}/questions",
    response_model=list[ResearchQuestionResponse],
)
def list_project_questions(
    project_id: int,
    db: DbSession,
):
    project = repository.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    return repository.get_questions_for_project(
        db,
        project_id,
    )


@router.post(
    "/projects/{project_id}/questions",
    response_model=ResearchQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_question(
    project_id: int,
    question_data: ResearchQuestionCreate,
    db: DbSession,
):
    project = repository.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    if question_data.parent_question_id is not None:

        parent = repository.get_question(
            db,
            question_data.parent_question_id,
        )

        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent research question not found",
            )

        if parent.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent question belongs to another project",
            )

    return repository.create_question(
        db=db,
        project_id=project_id,
        question_data=question_data,
    )


@router.get(
    "/questions/{question_id}",
    response_model=ResearchQuestionResponse,
)
def read_question(
    question_id: int,
    db: DbSession,
):
    question = repository.get_question(
        db,
        question_id,
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research question not found",
        )

    return question


@router.patch(
    "/questions/{question_id}",
    response_model=ResearchQuestionResponse,
)

def update_question_endpoint(
    question_id: int,
    question_data: ResearchQuestionUpdate,
    db: DbSession,
):
    question = repository.get_question(db, question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research question not found",
        )

    return repository.update_question(
        db=db,
        question=question,
        question_data=question_data,
    )


@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question_endpoint(
    question_id: int,
    db: DbSession,
):
    question = repository.get_question(db, question_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research question not found",
        )

    repository.delete_question(db, question)
    return None

