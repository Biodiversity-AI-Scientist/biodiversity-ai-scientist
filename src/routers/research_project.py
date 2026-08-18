from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import research_project as repository
from src.schemas.research_project import (
    ResearchProjectCreate,
    ResearchProjectResponse,
    ResearchProjectUpdate,
)

router = APIRouter(
    prefix="/projects",
    tags=["Research projects"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "",
    response_model=ResearchProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new ResearchProject",
)
def create_project(
    project_data: ResearchProjectCreate,
    db: DbSession,
):
    return repository.create_project(
        db=db,
        project_data=project_data,
    )


@router.get(
    "",
    response_model=list[ResearchProjectResponse],
    summary="List ResearchProjects (filters out archived projects by default)",
)
def list_projects(
    db: DbSession,
    include_archived: bool = Query(default=False, description="Include archived/hidden projects"),
):
    return repository.get_projects(db, include_archived=include_archived)


@router.get(
    "/{project_id}",
    response_model=ResearchProjectResponse,
    summary="Get single ResearchProject by ID",
)
def read_project(
    project_id: int,
    db: DbSession,
):
    project = repository.get_project(
        db=db,
        project_id=project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )

    return project


@router.patch(
    "/{project_id}",
    response_model=ResearchProjectResponse,
    summary="Update ResearchProject attributes",
)
def update_project(
    project_id: int,
    data: ResearchProjectUpdate,
    db: DbSession,
):
    project = repository.update_project(db, project_id, data)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )
    return project


@router.post(
    "/{project_id}/archive",
    response_model=ResearchProjectResponse,
    summary="Archive and hide a ResearchProject",
)
def archive_project(
    project_id: int,
    db: DbSession,
):
    project = repository.archive_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )
    return project


@router.post(
    "/{project_id}/unarchive",
    response_model=ResearchProjectResponse,
    summary="Unarchive and restore a ResearchProject",
)
def unarchive_project(
    project_id: int,
    db: DbSession,
):
    project = repository.unarchive_project(db, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research project not found",
        )
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a ResearchProject and all child entities",
)
def delete_project(
    project_id: int,
    db: DbSession,
):
    try:
        deleted = repository.delete_project(db, project_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research project not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
