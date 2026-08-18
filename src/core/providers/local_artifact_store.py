"""
Local Filesystem ArtifactStore Implementation.

Stores files in an immutable, project-partitioned directory tree on local storage:
  {base_dir}/projects/project_{project_id}/{artifact_type}/{filename}
"""
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.contracts.artifact_store import ArtifactStore, StoredArtifactInfo


class LocalArtifactStore(ArtifactStore):
    def __init__(self, base_dir: str | Path | None = None):
        self._base_dir = Path(base_dir or "/tmp/bais_artifacts")
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def store_name(self) -> str:
        return "local_artifact_store"

    def _get_target_dir(self, project_id: int, artifact_type: str) -> Path:
        target_dir = self._base_dir / f"projects/project_{project_id}" / artifact_type
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def store_file(
        self,
        source_path: str | Path,
        artifact_type: str,
        project_id: int,
        filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredArtifactInfo:
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Source file {source_path} does not exist")

        dest_name = filename or src.name
        target_dir = self._get_target_dir(project_id, artifact_type)
        dest_path = target_dir / dest_name

        shutil.copy2(src, dest_path)
        sha256 = self.compute_sha256(dest_path)
        size_bytes = dest_path.stat().st_size
        uri = f"local://{dest_path.absolute()}"

        return StoredArtifactInfo(
            uri=uri,
            filename=dest_name,
            artifact_type=artifact_type,
            sha256=sha256,
            size_bytes=size_bytes,
            stored_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    def store_bytes(
        self,
        data: bytes,
        artifact_type: str,
        project_id: int,
        filename: str,
        metadata: dict[str, Any] | None = None,
    ) -> StoredArtifactInfo:
        target_dir = self._get_target_dir(project_id, artifact_type)
        dest_path = target_dir / filename

        with open(dest_path, "wb") as f:
            f.write(data)

        sha256 = self.compute_sha256(data)
        size_bytes = len(data)
        uri = f"local://{dest_path.absolute()}"

        return StoredArtifactInfo(
            uri=uri,
            filename=filename,
            artifact_type=artifact_type,
            sha256=sha256,
            size_bytes=size_bytes,
            stored_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    def retrieve_path(self, uri: str) -> Path:
        if uri.startswith("local://"):
            p = Path(uri[len("local://"):])
        else:
            p = Path(uri)
        if not p.exists():
            raise FileNotFoundError(f"Artifact URI {uri} not found at {p}")
        return p

    def read_bytes(self, uri: str) -> bytes:
        p = self.retrieve_path(uri)
        with open(p, "rb") as f:
            return f.read()
