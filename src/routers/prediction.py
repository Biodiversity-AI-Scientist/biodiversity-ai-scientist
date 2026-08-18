from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import prediction as repository
from src.schemas.prediction import (
    PredictionCreate,
    PredictionResponse,
)


router = APIRouter(
    tags=["Predictions"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/hypotheses/{hypothesis_id}/predictions",
    response_model=list[PredictionResponse],
)
def list_hypothesis_predictions(
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

    return repository.get_predictions_for_hypothesis(
        db,
        hypothesis_id,
    )


@router.post(
    "/hypotheses/{hypothesis_id}/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hypothesis_prediction(
    hypothesis_id: int,
    prediction_data: PredictionCreate,
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

    return repository.create_prediction(
        db=db,
        hypothesis_id=hypothesis_id,
        prediction_data=prediction_data,
    )
