from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.research_project import ResearchProject
    from src.models.research_plan import ResearchPlan
    from src.models.result import Result


class ResearchAgendaItem(Base):
    __tablename__ = "research_agenda_item"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="open_question",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="open",
        index=True,
    )

    origin_project_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=True,
        index=True,
    )

    origin_research_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_plan.id"),
        nullable=True,
        index=True,
    )

    origin_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("result.id"),
        nullable=True,
        index=True,
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    current_evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    known_limitations: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    follow_up_opportunities: Mapped[str | None] = mapped_column(
        Text,
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

    # Relationships
    origin_project: Mapped["ResearchProject | None"] = relationship(
        "ResearchProject",
        foreign_keys=[origin_project_id],
    )
    origin_research_plan: Mapped["ResearchPlan | None"] = relationship(
        "ResearchPlan",
        foreign_keys=[origin_research_plan_id],
    )
    origin_result: Mapped["Result | None"] = relationship(
        "Result",
        foreign_keys=[origin_result_id],
    )
