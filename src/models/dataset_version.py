from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_version"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    version_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    source_system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    selection_definition: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    member_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    grouping_keys: Mapped[list[Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    manifest_uri: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    manifest_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

