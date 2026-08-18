from typing import Any

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ClaimEdge(Base):
    __tablename__ = "claim_edge"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    source_claim_id: Mapped[int] = mapped_column(
        ForeignKey("claim.id"),
        nullable=False,
        index=True,
    )

    target_claim_id: Mapped[int] = mapped_column(
        ForeignKey("claim.id"),
        nullable=False,
        index=True,
    )

    relation: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    qualification: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

