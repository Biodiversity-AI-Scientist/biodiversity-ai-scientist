from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class ResearchProject(Base):
    __tablename__ = "research_project"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    objective: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


    questions: Mapped[list["ResearchQuestion"]] = relationship(
        "ResearchQuestion",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    brainstorming_sessions: Mapped[list["BrainstormingSession"]] = relationship(
        "BrainstormingSession",
        back_populates="project",
        cascade="all, delete-orphan",
    )

