from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import hypothesis as repository
from src.schemas.hypothesis import (
    HypothesisCreate,
    HypothesisResponse,
    HypothesisUpdate,
)



router = APIRouter(
    tags=["Hypotheses"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/projects/{project_id}/hypotheses",
    response_model=list[HypothesisResponse],
)
def list_project_hypotheses(
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

    return repository.get_hypotheses_for_project(
        db,
        project_id,
    )


@router.get(
    "/questions/{question_id}/hypotheses",
    response_model=list[HypothesisResponse],
)
def list_question_hypotheses(
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

    return repository.get_hypotheses_for_question(
        db,
        question_id,
    )


@router.post(
    "/questions/{question_id}/hypotheses",
    response_model=HypothesisResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question_hypothesis(
    question_id: int,
    hypothesis_data: HypothesisCreate,
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

    return repository.create_hypothesis(
        db=db,
        question_id=question_id,
        hypothesis_data=hypothesis_data,
    )


@router.get(
    "/hypotheses/{hypothesis_id}",
    response_model=HypothesisResponse,
)
def read_hypothesis(
    hypothesis_id: int,
    db: DbSession,
):
    hypothesis = repository.get_hypothesis(
        db,
        hypothesis_id,
    )

    if hypothesis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hypothesis not found",
        )

    return hypothesis


@router.patch(
    "/hypotheses/{hypothesis_id}",
    response_model=HypothesisResponse,
)

def update_hypothesis_endpoint(
    hypothesis_id: int,
    hypothesis_data: HypothesisUpdate,
    db: DbSession,
):
    hypothesis = repository.get_hypothesis(db, hypothesis_id)
    if hypothesis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hypothesis not found",
        )

    return repository.update_hypothesis(
        db=db,
        hypothesis=hypothesis,
        hypothesis_data=hypothesis_data,
    )


@router.delete(
    "/hypotheses/{hypothesis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_hypothesis_endpoint(
    hypothesis_id: int,
    db: DbSession,
):
    hypothesis = repository.get_hypothesis(db, hypothesis_id)
    if hypothesis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hypothesis not found",
        )

    repository.delete_hypothesis(db, hypothesis)
    return None

