import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import research_agenda as repository
from src.schemas.research_agenda import (
    ResearchAgendaItemCreate,
    ResearchAgendaItemResponse,
    ResearchAgendaItemUpdate,
)
from src.services.research_program import (
    get_findshell_publications_index,
    search_papers_api,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Research Agenda & Program Intelligence"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/research-agenda",
    response_model=list[ResearchAgendaItemResponse],
)
def list_research_agenda_items(
    db: DbSession,
    status_filter: str | None = Query(default=None, alias="status"),
    type_filter: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ResearchAgendaItemResponse]:
    # Ensure default agenda items are seeded if DB is empty
    repository.seed_default_research_agenda_if_empty(db)
    items = repository.list_agenda_items(
        db=db,
        status_filter=status_filter,
        type_filter=type_filter,
        limit=limit,
    )
    return [ResearchAgendaItemResponse.model_validate(item) for item in items]


@router.post(
    "/research-agenda",
    response_model=ResearchAgendaItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_agenda_item(
    item_data: ResearchAgendaItemCreate,
    db: DbSession,
) -> ResearchAgendaItemResponse:
    item = repository.create_agenda_item(db=db, item_data=item_data)
    return ResearchAgendaItemResponse.model_validate(item)


@router.get(
    "/research-agenda/{item_id}",
    response_model=ResearchAgendaItemResponse,
)
def get_research_agenda_item(
    item_id: int,
    db: DbSession,
) -> ResearchAgendaItemResponse:
    item = repository.get_agenda_item(db, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchAgendaItem #{item_id} not found",
        )
    return ResearchAgendaItemResponse.model_validate(item)


@router.patch(
    "/research-agenda/{item_id}",
    response_model=ResearchAgendaItemResponse,
)
def update_research_agenda_item(
    item_id: int,
    update_data: ResearchAgendaItemUpdate,
    db: DbSession,
) -> ResearchAgendaItemResponse:
    item = repository.get_agenda_item(db, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ResearchAgendaItem #{item_id} not found",
        )
    updated = repository.update_agenda_item(db, item, update_data)
    return ResearchAgendaItemResponse.model_validate(updated)


@router.get(
    "/research-program/literature-search",
)
def search_research_program_literature(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=5, ge=1, le=20),
):
    results = search_papers_api(query=q, limit=limit)
    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get(
    "/research-program/publications",
)
def list_findshell_publications():
    pubs = get_findshell_publications_index()
    return {
        "count": len(pubs),
        "publications": pubs,
    }
