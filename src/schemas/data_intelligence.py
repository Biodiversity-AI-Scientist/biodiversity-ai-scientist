from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ModelNetworkSummary(BaseModel):
    taxon_name: str
    taxon_level: str | None = None  # GENUS, SUBFAMILY, FAMILY, ORDER
    taxon_level_result: str | None = None  # SPECIES, GENUS
    view_type: str | None = None  # Front, Back, Outside, Dorsal
    model_path: str | None = None
    is_default: bool = True
    created_at: datetime | None = None

    model_config = ConfigDict(extra="ignore")


class TaxonImageSummary(BaseModel):
    taxon_name: str
    rank: str | None = None
    total_images: int = 0
    total_species: int = 0
    species_with_images: int = 0
    view_distribution: dict[str, int] = Field(default_factory=dict)
    source_distribution: dict[str, int] = Field(default_factory=dict)
    habitat_flags: dict[str, bool] = Field(default_factory=dict)
    worms_status_distribution: dict[str, int] = Field(default_factory=dict)
    existing_models: list[ModelNetworkSummary] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class SpeciesImageCount(BaseModel):
    species_name: str
    genus_name: str
    aphia_id: int | None = None
    worms_status: str | None = None
    total_images: int = 0
    transformed_images: int = 0
    views: list[str] = Field(default_factory=list)
    meets_threshold: bool = True

    model_config = ConfigDict(extra="ignore")


class GenusImageCountSummary(BaseModel):
    genus_name: str
    family_name: str | None = None
    order_name: str | None = None
    class_name: str | None = None
    total_species: int = 0
    species_above_threshold: int = 0
    total_images: int = 0
    min_images_per_species: int = 0
    max_images_per_species: int = 0
    avg_images_per_species: float = 0.0
    imbalance_ratio: float = 0.0
    is_feasible_for_classifier: bool = False
    has_existing_model: bool = False
    existing_model_views: list[str] = Field(default_factory=list)
    existing_models: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class DatasetClassDistribution(BaseModel):
    dataset_name: str
    genus: str | None = None
    total_images: int = 0
    total_classes: int = 0
    class_counts: dict[str, int] = Field(default_factory=dict)
    min_class_count: int = 0
    max_class_count: int = 0
    imbalance_ratio: float = 0.0

    model_config = ConfigDict(extra="ignore")


class SourceSummaryItem(BaseModel):
    source_name: str
    image_count: int
    shell_record_count: int = 0
    species_count: int = 0

    model_config = ConfigDict(extra="ignore")


class DatasetVersionSummary(BaseModel):
    dataset_name: str
    genus: str | None = None
    create_script: str | None = None
    total_transforms: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(extra="ignore")


class ModelPerformanceSummary(BaseModel):
    taxon_name: str
    model_name: str | None = None
    view_type: str | None = None
    category_taxon: str | None = None
    accuracy: float | None = None
    precision: float | None = None
    num_tests: int | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(extra="ignore")


class FeasibilityEvaluationRequest(BaseModel):
    family_name: str | None = None
    order_name: str | None = None
    class_name: str | None = None
    min_species: int = Field(default=3, ge=1)
    min_images_per_species: int = Field(default=10, ge=1)
    max_imbalance_ratio: float = Field(default=10.0, gt=0.0)
    exclude_existing_models: bool = False


class FeasibilityEvaluationResponse(BaseModel):
    criteria: FeasibilityEvaluationRequest
    candidate_genera: list[GenusImageCountSummary]
    recommended_novel_genera: list[str] = Field(default_factory=list)
    recommended_existing_model_genera: list[str] = Field(default_factory=list)
    total_genera_evaluated: int = 0
