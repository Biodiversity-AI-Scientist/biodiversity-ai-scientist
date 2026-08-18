from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Result(Base):
    __tablename__ = "result"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    analysis_run_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_run.id"),
        nullable=False,
        index=True,
    )

    result_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    uncertainty: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    diagnostics: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

