
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Claim(Base):
    __tablename__ = "claim"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_question.id"),
        nullable=True,
        index=True,
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)

    scope: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    claim_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    epistemic_status: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="unresolved",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

