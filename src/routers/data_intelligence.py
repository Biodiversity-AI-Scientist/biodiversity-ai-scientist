from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_dwh_db
from src.schemas.data_intelligence import (
    DatasetClassDistribution,
    DatasetVersionSummary,
    FeasibilityEvaluationRequest,
    FeasibilityEvaluationResponse,
    GenusImageCountSummary,
    ModelNetworkSummary,
    ModelPerformanceSummary,
    SourceSummaryItem,
    SpeciesImageCount,
    TaxonImageSummary,
)
from src.services import data_intelligence as service

router = APIRouter(
    prefix="/data-intelligence",
    tags=["Local Data Intelligence"],
)

DwhDbSession = Annotated[
    Session,
    Depends(get_dwh_db),
]


@router.get(
    "/taxon-summary",
    response_model=TaxonImageSummary,
)
def get_taxon_summary(
    taxon: str = Query(min_length=1, description="Name of the taxon (Genus, Family, etc.)"),
    rank: str | None = Query(default=None, description="Optional taxonomic rank (e.g. Genus, Family, Order, Class)"),
    db: DwhDbSession = None,
) -> TaxonImageSummary:
    try:
        return service.get_taxon_image_summary(db=db, taxon_name=taxon, rank=rank)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch taxon summary: {exc}",
        ) from exc


@router.get(
    "/species-counts",
    response_model=list[SpeciesImageCount],
)
def get_species_counts(
    genus: str = Query(min_length=1, description="Genus name"),
    min_images: int = Query(default=1, ge=0, description="Minimum total images filter"),
    db: DwhDbSession = None,
) -> list[SpeciesImageCount]:
    try:
        return service.get_species_image_counts(db=db, genus_name=genus, min_images=min_images)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch species image counts: {exc}",
        ) from exc


@router.get(
    "/genus-counts",
    response_model=list[GenusImageCountSummary],
)
def get_genus_counts(
    family: str | None = Query(default=None, description="Optional Family or parent taxon name"),
    order: str | None = Query(default=None, description="Optional Order name"),
    class_name: str | None = Query(default=None, description="Optional Class name"),
    min_species: int = Query(default=1, ge=1, description="Minimum species per genus"),
    min_images_per_species: int = Query(default=5, ge=1, description="Threshold for images per species"),
    db: DwhDbSession = None,
) -> list[GenusImageCountSummary]:
    try:
        return service.get_genus_image_counts(
            db=db,
            family_name=family,
            order_name=order,
            class_name=class_name,
            min_species=min_species,
            min_images_per_species=min_images_per_species,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch genus image counts: {exc}",
        ) from exc


@router.get(
    "/dataset-distribution",
    response_model=DatasetClassDistribution,
)
def get_dataset_distribution(
    dataset: str = Query(min_length=1, description="Dataset name in ImageDatasets"),
    db: DwhDbSession = None,
) -> DatasetClassDistribution:
    try:
        return service.get_dataset_class_distribution(db=db, dataset_name=dataset)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dataset distribution: {exc}",
        ) from exc


@router.get(
    "/dataset-sources",
    response_model=list[SourceSummaryItem],
)
def get_dataset_sources(
    taxon: str | None = Query(default=None, description="Optional taxon/genus name"),
    dataset: str | None = Query(default=None, description="Optional dataset name"),
    db: DwhDbSession = None,
) -> list[SourceSummaryItem]:
    try:
        return service.get_dataset_source_summary(db=db, taxon_name=taxon, dataset_name=dataset)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dataset source summary: {exc}",
        ) from exc


@router.get(
    "/datasets",
    response_model=list[DatasetVersionSummary],
)
def get_datasets(
    taxon: str | None = Query(default=None, description="Optional taxon/genus filter"),
    db: DwhDbSession = None,
) -> list[DatasetVersionSummary]:
    try:
        return service.get_existing_dataset_versions(db=db, taxon_name=taxon)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch datasets: {exc}",
        ) from exc


@router.get(
    "/models",
    response_model=list[ModelPerformanceSummary],
)
def get_models(
    taxon: str = Query(min_length=1, description="Taxon name"),
    db: DwhDbSession = None,
) -> list[ModelPerformanceSummary]:
    try:
        return service.get_previous_model_summary(db=db, taxon_name=taxon)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch previous models: {exc}",
        ) from exc


@router.get(
    "/model-networks",
    response_model=list[ModelNetworkSummary],
)
def get_model_networks(
    taxon: str | None = Query(default=None, description="Optional Taxon filter"),
    level: str | None = Query(default=None, description="Optional TaxonLevel filter (e.g. GENUS, FAMILY, ORDER)"),
    db: DwhDbSession = None,
) -> list[ModelNetworkSummary]:
    try:
        return service.get_existing_model_networks(db=db, taxon_name=taxon, taxon_level=level)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch model networks: {exc}",
        ) from exc


@router.post(
    "/feasibility",
    response_model=FeasibilityEvaluationResponse,
)
def evaluate_feasibility(
    payload: FeasibilityEvaluationRequest,
    db: DwhDbSession = None,
) -> FeasibilityEvaluationResponse:
    try:
        return service.evaluate_classifier_feasibility(db=db, request=payload)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate classifier feasibility: {exc}",
        ) from exc
