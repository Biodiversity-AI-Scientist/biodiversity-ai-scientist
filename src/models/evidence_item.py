from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class EvidenceItem(Base):
    __tablename__ = "evidence_item"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claim.id"),
        nullable=False,
        index=True,
    )

    result_id: Mapped[int | None] = mapped_column(
        ForeignKey("result.id"),
        nullable=True,
        index=True,
    )

    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("source_document.id"),
        nullable=True,
        index=True,
    )

    artifact_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifact.id"),
        nullable=True,
        index=True,
    )

    direction: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    validity_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unreviewed",
    )

    independence_group: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    inferential_level: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    limitations: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

