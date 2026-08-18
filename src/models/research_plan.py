from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class ResearchPlan(Base):
    __tablename__ = "research_plan"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    brainstorming_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("brainstorming_session.id"),
        nullable=True,
        index=True,
    )

    parent_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_plan.id"),
        nullable=True,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
    )

    content: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    model_provenance: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    project = relationship("ResearchProject")
    brainstorming_session = relationship("BrainstormingSession")
    parent_plan = relationship("ResearchPlan", remote_side="ResearchPlan.id")
