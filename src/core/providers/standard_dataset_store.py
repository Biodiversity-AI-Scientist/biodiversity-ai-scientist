"""
Standard DatasetStore Implementation.

Resolves dataset versions and member manifests from the database or local storage.
"""
from typing import Any
from sqlalchemy.orm import Session

from src.core.contracts.dataset_store import (
    DatasetManifest,
    DatasetMemberInfo,
    DatasetStore,
)
from src.models import DatasetVersion


class StandardDatasetStore(DatasetStore):
    def __init__(self, db_session_factory=None):
        self._db_session_factory = db_session_factory

    @property
    def store_name(self) -> str:
        return "standard_dataset_store"

    def resolve_manifest(self, dataset_version_id: int) -> DatasetManifest:
        if not self._db_session_factory:
            return DatasetManifest(
                version_id=dataset_version_id,
                version_key=f"v_{dataset_version_id}",
                project_id=1,
                total_members=0,
                members=[],
            )

        db: Session = self._db_session_factory()
        try:
            version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
            if not version:
                return DatasetManifest(
                    version_id=dataset_version_id,
                    version_key=f"unknown_version_{dataset_version_id}",
                    project_id=0,
                    total_members=0,
                    members=[],
                )

            count = version.member_count or 0
            member_infos = []
            for i in range(count):
                member_infos.append(
                    DatasetMemberInfo(
                        member_id=f"specimen_{i+1}",
                        relative_path=f"specimens/specimen_{i+1}.jpg",
                        absolute_uri=f"file:///datasets/{version.id}/specimen_{i+1}.jpg",
                    )
                )

            return DatasetManifest(
                version_id=version.id,
                version_key=version.version_key,
                project_id=version.project_id,
                total_members=count,
                members=member_infos,
                manifest_uri=version.manifest_uri,
                manifest_sha256=version.manifest_sha256,
            )
        finally:
            db.close()

    def get_member_paths(self, dataset_version_id: int) -> list[str]:
        manifest = self.resolve_manifest(dataset_version_id)
        return [m.absolute_uri for m in manifest.members]
