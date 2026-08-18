from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import Hypothesis, Prediction
from src.schemas.prediction import PredictionCreate


def get_hypothesis(
    db: Session,
    hypothesis_id: int,
) -> Hypothesis | None:

    return db.get(
        Hypothesis,
        hypothesis_id,
    )


def get_predictions_for_hypothesis(
    db: Session,
    hypothesis_id: int,
) -> list[Prediction]:

    statement = (
        select(Prediction)
        .where(
            Prediction.hypothesis_id == hypothesis_id
        )
        .order_by(
            Prediction.id
        )
    )

    return list(
        db.scalars(statement).all()
    )


def create_prediction(
    db: Session,
    hypothesis_id: int,
    prediction_data: PredictionCreate,
) -> Prediction:

    prediction = Prediction(
        hypothesis_id=hypothesis_id,
        statement=prediction_data.statement,
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction
