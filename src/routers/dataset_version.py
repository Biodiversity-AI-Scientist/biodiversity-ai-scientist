from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import dataset_version as repository
from src.schemas.dataset_version import (
    DatasetVersionCreate,
    DatasetVersionResponse,
)


router = APIRouter(
    tags=["Dataset versions"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/projects/{project_id}/datasets",
    response_model=list[DatasetVersionResponse],
)
def list_project_datasets(
    project_id: int,
    db: DbSession,
):
    project = repository.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    return repository.get_datasets_for_project(
        db,
        project_id,
    )


@router.post(
    "/projects/{project_id}/datasets",
    response_model=DatasetVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project_dataset(
    project_id: int,
    dataset_data: DatasetVersionCreate,
    db: DbSession,
):
    project = repository.get_project(
        db,
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    existing = repository.get_dataset_by_version_key(
        db,
        dataset_data.version_key,
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset version_key already exists",
        )

    return repository.create_dataset_version(
        db=db,
        project_id=project_id,
        dataset_data=dataset_data,
    )


@router.get(
    "/datasets/{dataset_version_id}",
    response_model=DatasetVersionResponse,
)
def read_dataset_version(
    dataset_version_id: int,
    db: DbSession,
):
    dataset = repository.get_dataset_version(
        db,
        dataset_version_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset version not found",
        )

    return dataset
