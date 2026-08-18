from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatasetVersionCreate(BaseModel):
    version_key: str = Field(
        min_length=1,
        max_length=100,
    )

    source_system: str = Field(
        min_length=1,
        max_length=100,
    )

    selection_definition: dict[str, Any] | None = None

    member_count: int | None = Field(
        default=None,
        ge=0,
    )

    grouping_keys: list[Any] | None = None

    manifest_uri: str | None = Field(
        default=None,
        max_length=1024,
    )

    manifest_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
    )


class DatasetVersionResponse(BaseModel):
    id: int
    project_id: int
    version_key: str
    source_system: str
    selection_definition: dict[str, Any] | None
    member_count: int | None
    grouping_keys: list[Any] | None
    manifest_uri: str | None
    manifest_sha256: str | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
