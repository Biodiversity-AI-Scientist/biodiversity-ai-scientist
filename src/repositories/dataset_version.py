from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import DatasetVersion, ResearchProject
from src.schemas.dataset_version import DatasetVersionCreate


def get_project(
    db: Session,
    project_id: int,
) -> ResearchProject | None:

    return db.get(
        ResearchProject,
        project_id,
    )


def get_dataset_version(
    db: Session,
    dataset_version_id: int,
) -> DatasetVersion | None:

    return db.get(
        DatasetVersion,
        dataset_version_id,
    )


def get_dataset_by_version_key(
    db: Session,
    version_key: str,
) -> DatasetVersion | None:

    statement = (
        select(DatasetVersion)
        .where(
            DatasetVersion.version_key == version_key
        )
    )

    return db.scalar(statement)


def get_datasets_for_project(
    db: Session,
    project_id: int,
) -> list[DatasetVersion]:

    statement = (
        select(DatasetVersion)
        .where(
            DatasetVersion.project_id == project_id
        )
        .order_by(
            DatasetVersion.created_at.desc(),
            DatasetVersion.id.desc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def create_dataset_version(
    db: Session,
    project_id: int,
    dataset_data: DatasetVersionCreate,
) -> DatasetVersion:

    dataset = DatasetVersion(
        project_id=project_id,
        version_key=dataset_data.version_key,
        source_system=dataset_data.source_system,
        selection_definition=dataset_data.selection_definition,
        member_count=dataset_data.member_count,
        grouping_keys=dataset_data.grouping_keys,
        manifest_uri=dataset_data.manifest_uri,
        manifest_sha256=dataset_data.manifest_sha256,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset
