from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.research_project import ResearchProject


class BrainstormingSession(Base):
    __tablename__ = "brainstorming_session"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    initial_idea: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    messages: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    model_provenance: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
    )

    research_plan: Mapped[dict[str, Any] | None] = mapped_column(
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

    project: Mapped["ResearchProject"] = relationship(
        "ResearchProject",
        back_populates="brainstorming_sessions",
    )

    @property
    def candidates(self) -> list[dict[str, Any]]:
        result = []
        for msg in self.messages or []:
            if isinstance(msg, dict) and "candidates" in msg and isinstance(msg["candidates"], list):
                result.extend(msg["candidates"])
        return result

