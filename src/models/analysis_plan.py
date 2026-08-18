from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class AnalysisPlan(Base):
    """
    Internal/legacy entity name retained for API, schema, and database compatibility.

    Scientifically, this entity represents an **Experiment**: the pre-specification
    of a concrete computational or empirical procedure intended to generate evidence
    for a specific ResearchQuestion and Hypothesis.

    Distinction:
    - ResearchPlan: Overall scientific study strategy (narrative, questions, stages).
    - AnalysisPlan (Experiment): Discrete, testable evidence-generating experimental procedure.
    - AnalysisRun (Experiment Run): One actual execution of this experiment.
    """
    __tablename__ = "analysis_plan"


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("research_question.id"),
        nullable=False,
        index=True,
    )

    hypothesis_id: Mapped[int | None] = mapped_column(
        ForeignKey("hypothesis.id"),
        nullable=True,
        index=True,
    )

    dataset_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("dataset_version.id"),
        nullable=True,
        index=True,
    )

    estimand: Mapped[str | None] = mapped_column(Text, nullable=True)

    method: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    assumptions: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    parameters: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    exploratory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="proposed",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )


