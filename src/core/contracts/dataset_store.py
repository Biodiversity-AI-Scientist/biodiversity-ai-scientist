"""
Generic Core Contract: DatasetStore

Defines abstract interface for dataset manifest resolution, member access,
and specimen image discovery without hardcoded local or NFS filesystem paths.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetMemberInfo:
    member_id: str
    relative_path: str
    absolute_uri: str
    taxon_name: str | None = None
    view_orientation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetManifest:
    version_id: int
    version_key: str
    project_id: int
    total_members: int
    members: list[DatasetMemberInfo] = field(default_factory=list)
    manifest_uri: str | None = None
    manifest_sha256: str | None = None


class DatasetStore(ABC):
    @property
    @abstractmethod
    def store_name(self) -> str:
        """Name of the dataset store."""
        ...

    @abstractmethod
    def resolve_manifest(self, dataset_version_id: int) -> DatasetManifest:
        """Resolves full dataset manifest with member records."""
        ...

    @abstractmethod
    def get_member_paths(self, dataset_version_id: int) -> list[str]:
        """Returns list of accessible file paths or URIs for dataset members."""
        ...
