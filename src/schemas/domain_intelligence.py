from typing import Any
from pydantic import BaseModel, Field


class LiteratureItem(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    source: str  # e.g., "arXiv", "bioRxiv", "LocalPapersLibrary"
    doi: str | None = None
    url: str | None = None
    abstract: str | None = None
    relevance_note: str | None = None


class WormsTaxonomicRecord(BaseModel):
    aphia_id: int | None = None
    scientific_name: str
    authority: str | None = None
    rank: str | None = None
    status: str = "unknown"  # "accepted", "unaccepted", "synonym"
    valid_aphia_id: int | None = None
    valid_name: str | None = None
    valid_authority: str | None = None
    kingdom: str | None = None
    phylum: str | None = None
    class_name: str | None = None
    order: str | None = None
    family: str | None = None
    genus: str | None = None
    is_marine: bool | None = None
    synonyms: list[str] = Field(default_factory=list)
    url: str | None = None


class TaxonBiologicalContext(BaseModel):
    taxon_name: str
    worms: WormsTaxonomicRecord | None = None
    taxonomic_stability: str = "stable"  # "stable", "controversial", "complex_synonymy"
    has_cryptic_complexes: bool = False
    morphological_challenges: list[str] = Field(default_factory=list)
    molecular_notes: str | None = None
    literature_citations: list[LiteratureItem] = Field(default_factory=list)
    unresolved_knowledge_gaps: list[str] = Field(default_factory=list)


class TaxonPriorityComparison(BaseModel):
    taxon_a: str
    taxon_b: str
    taxon_a_summary: dict[str, Any]
    taxon_b_summary: dict[str, Any]
    recommended_priority: str  # taxon_a or taxon_b
    justification: str
    comparative_dimensions: dict[str, Any]
