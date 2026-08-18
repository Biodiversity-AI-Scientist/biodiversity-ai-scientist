from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from src.schemas.domain_intelligence import TaxonBiologicalContext, LiteratureItem
from src.schemas.research_agenda import ResearchAgendaItemSummary


class IntelligenceLayer(str, Enum):
    DATA = "data_intelligence"
    RESEARCH_PROGRAM = "research_program_intelligence"
    DOMAIN = "domain_intelligence"


class ProvenanceRecord(BaseModel):
    source_type: str = Field(..., description="E.g., DWH_SQL, FIND_SHELL_RESULT, WORMS_API, ARX_PREPRINT, LOCAL_PAPERS")
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    query_or_endpoint: str | None = None
    confidence_or_status: str | None = None


class DataIntelligenceSection(BaseModel):
    is_active: bool = True
    status: str = "ok"  # ok, no_records, skipped, degraded
    unmodeled_taxa_available: list[str] = Field(default_factory=list)
    focal_taxon_images: int = 0
    focal_taxon_species_count: int = 0
    focal_taxon_usable_species: int = 0
    models_already_exist: bool = False
    rich_dwh_context: str | None = None
    data_gaps: list[str] = Field(default_factory=list)
    provenance: ProvenanceRecord | None = None



class ResearchProgramIntelligenceSection(BaseModel):
    is_active: bool = True
    status: str = "ok"  # ok, no_records, skipped, degraded
    active_agenda_items: list[ResearchAgendaItemSummary] = Field(default_factory=list)
    previous_findings: list[str] = Field(default_factory=list)
    open_methodological_questions: list[str] = Field(default_factory=list)
    rich_program_context: str | None = None
    limitations_noted: list[str] = Field(default_factory=list)
    provenance: ProvenanceRecord | None = None



class DomainIntelligenceSection(BaseModel):
    is_active: bool = True
    status: str = "ok"  # ok, no_records, skipped, degraded
    focal_taxon: str | None = None
    taxonomic_status: str | None = None
    aphia_id: int | None = None
    synonyms: list[str] = Field(default_factory=list)
    has_cryptic_complexes: bool = False
    morphological_challenges: list[str] = Field(default_factory=list)
    relevant_literature: list[LiteratureItem] = Field(default_factory=list)
    conflicting_evidence: list[str] = Field(default_factory=list)
    provenance: ProvenanceRecord | None = None


class RetrievalSummary(BaseModel):
    activated_layers: list[IntelligenceLayer] = Field(default_factory=list)
    skipped_layers: list[IntelligenceLayer] = Field(default_factory=list)
    routing_rationale: str = ""
    latency_ms: float = 0.0


class ResearchIntelligencePacket(BaseModel):
    research_idea: str = ""
    project_context: dict[str, Any] = Field(default_factory=dict)
    data_intelligence: DataIntelligenceSection | None = None
    research_program_intelligence: ResearchProgramIntelligenceSection | None = None
    domain_intelligence: DomainIntelligenceSection | None = None
    uncertainties: list[str] = Field(default_factory=list)
    retrieval_summary: RetrievalSummary = Field(default_factory=RetrievalSummary)
    assembled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
