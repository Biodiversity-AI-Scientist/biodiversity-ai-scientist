"""
Generic Core Contract: ArtifactStore

Defines abstract interface for storing, hashing, retrieving, and verifying
scientific artifacts produced by experiments (models, plots, embeddings, matrices).
"""
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO


@dataclass(frozen=True)
class StoredArtifactInfo:
    uri: str
    filename: str
    artifact_type: str
    sha256: str
    size_bytes: int
    stored_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class ArtifactStore(ABC):
    @property
    @abstractmethod
    def store_name(self) -> str:
        """Name of the artifact store implementation."""
        ...

    @abstractmethod
    def store_file(
        self,
        source_path: str | Path,
        artifact_type: str,
        project_id: int,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredArtifactInfo:
        """Persists a file into the artifact store and returns storage metadata."""
        ...

    @abstractmethod
    def store_bytes(
        self,
        data: bytes,
        artifact_type: str,
        project_id: int,
        filename: str,
        metadata: dict[str, Any] | None = None,
    ) -> StoredArtifactInfo:
        """Persists raw bytes into the artifact store."""
        ...

    @abstractmethod
    def retrieve_path(self, uri: str) -> Path:
        """Resolves an artifact URI to a local readable filesystem Path."""
        ...

    @abstractmethod
    def read_bytes(self, uri: str) -> bytes:
        """Reads raw binary content from an artifact URI."""
        ...

    @staticmethod
    def compute_sha256(data_or_path: bytes | str | Path) -> str:
        """Computes SHA-256 hex digest of file or bytes."""
        hasher = hashlib.sha256()
        if isinstance(data_or_path, (str, Path)):
            p = Path(data_or_path)
            with open(p, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
        elif isinstance(data_or_path, bytes):
            hasher.update(data_or_path)
        else:
            raise TypeError("Expected bytes or Path/str")
        return hasher.hexdigest()

    def verify_checksum(self, uri: str, expected_sha256: str) -> bool:
        """Verifies that an artifact's content matches the expected SHA-256 digest."""
        try:
            content = self.read_bytes(uri)
            actual = self.compute_sha256(content)
            return actual.lower() == expected_sha256.lower()
        except Exception:
            return False
