from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class AnalysisRun(Base):
    """
    Internal/legacy entity name retained for API, schema, and database compatibility.

    Scientifically, this entity represents an **Experiment Run**: one actual execution
    of an Experiment (AnalysisPlan), capturing execution lifecycle state (pending, running,
    completed, failed), timestamps, actual runtime parameters, host environment metadata,
    empirical Results, and failure diagnostics.
    """
    __tablename__ = "analysis_run"


    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    analysis_plan_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_plan.id"),
        nullable=False,
        index=True,
    )

    dataset_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("dataset_version.id"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )

    tool_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    source_code_commit: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    generated_code_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    container_image_digest: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    parameters: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    random_seeds: Mapped[list[Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    hardware_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    execution_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    error_details: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
