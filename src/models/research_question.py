from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class ResearchQuestion(Base):
    __tablename__ = "research_question"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    parent_question_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_question.id"),
        nullable=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    inferential_level: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="open",
    )

    source: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        default="user",
    )

    brainstorming_session_id: Mapped[int | None] = mapped_column(
        ForeignKey("brainstorming_session.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    project = relationship(
        "ResearchProject",
        back_populates="questions",
    )

    parent_question = relationship(
        "ResearchQuestion",
        remote_side="ResearchQuestion.id",
    )
