from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Hypothesis(Base):
    __tablename__ = "hypothesis"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    question_id: Mapped[int] = mapped_column(
        ForeignKey("research_question.id"),
        nullable=False,
        index=True,
    )

    statement: Mapped[str] = mapped_column(Text, nullable=False)

    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="proposed",
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

