from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityImplementationBase(BaseModel):
    implementation_key: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=255)
    provider: str = Field(default="core_engine", max_length=100)
    adapter_module: str | None = Field(default=None, max_length=255)
    backend_environment: str = Field(default="local_host", max_length=100)
    runtime_version: str | None = Field(default=None, max_length=64)
    implementation_scope: str = Field(default="generic_core", max_length=64)
    availability: str = Field(default="installed", max_length=32)
    validation_status: str = Field(default="known", max_length=32)
    is_default: bool = False
    execution_parameters: dict[str, Any] | None = None


class CapabilityImplementationCreate(CapabilityImplementationBase):
    pass


class CapabilityImplementationUpdate(BaseModel):
    display_name: str | None = None
    provider: str | None = None
    adapter_module: str | None = None
    backend_environment: str | None = None
    runtime_version: str | None = None
    implementation_scope: str | None = None
    availability: str | None = None
    validation_status: str | None = None
    is_default: bool | None = None
    execution_parameters: dict[str, Any] | None = None


class CapabilityImplementationResponse(CapabilityImplementationBase):
    id: int
    scientific_capability_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScientificCapabilityBase(BaseModel):
    capability_key: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=255)
    scientific_purpose: str = Field(min_length=1)
    domain: str = Field(default="biodiversity_informatics", max_length=64)
    subdomain: str | None = Field(default=None, max_length=64)
    ebv_dimension: str | None = Field(default=None, max_length=64)
    capability_scope: str = Field(default="generic_core", max_length=64)
    is_generic: bool = True
    scientific_maturity: str = Field(default="installed", max_length=32)
    knowledge_status: str = Field(default="known", max_length=32)
    availability: str = Field(default="installed", max_length=32)
    expected_evidence_types: list[str] | None = None
    preconditions: list[str] | None = None
    scientific_assumptions: list[str] | None = None
    scientific_constraints: list[str] | None = None
    scientific_tasks: str | None = None
    typical_duration: str | None = Field(default=None, max_length=64)
    reproducibility_level: str = Field(default="deterministic", max_length=64)
    modifies_data: bool = False
    creates_result: bool = True
    creates_artifact: bool = True
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    input_types: list[Any] | None = None
    output_types: list[Any] | None = None
    default_parameters: dict[str, Any] | None = None
    is_enabled: bool = True


class ScientificCapabilityCreate(ScientificCapabilityBase):
    implementations: list[CapabilityImplementationCreate] = Field(default_factory=list)


class ScientificCapabilityUpdate(BaseModel):
    display_name: str | None = None
    scientific_purpose: str | None = None
    domain: str | None = None
    subdomain: str | None = None
    ebv_dimension: str | None = None
    capability_scope: str | None = None
    is_generic: bool | None = None
    scientific_maturity: str | None = None
    knowledge_status: str | None = None
    availability: str | None = None
    expected_evidence_types: list[str] | None = None
    preconditions: list[str] | None = None
    scientific_assumptions: list[str] | None = None
    scientific_constraints: list[str] | None = None
    scientific_tasks: str | None = None
    typical_duration: str | None = None
    reproducibility_level: str | None = None
    modifies_data: bool | None = None
    creates_result: bool | None = None
    creates_artifact: bool | None = None
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    input_types: list[Any] | None = None
    output_types: list[Any] | None = None
    default_parameters: dict[str, Any] | None = None
    is_enabled: bool | None = None


class ScientificCapabilityResponse(ScientificCapabilityBase):
    id: int
    application_id: int
    created_at: datetime
    implementations: list[CapabilityImplementationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CapabilitySelectionResponse(BaseModel):
    id: int
    investigation_step_id: int
    selected_capability_id: int | None = None
    eligible_capability_ids: list[int] | None = None
    selection_method: str
    scientific_rationale: str | None = None
    rejected_alternatives: list[dict[str, Any]] | None = None
    known_limitations: str | None = None
    researcher_status: str
    llm_provenance: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    selected_capability: ScientificCapabilityResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class CapabilitySelectionOverrideRequest(BaseModel):
    selected_capability_id: int | None = Field(default=None, description="Capability ID to manually select, or None if setting gap")
    scientific_rationale: str = Field(min_length=1, description="Researcher rationale for override or manual selection")
    researcher_status: str = Field(default="override", description="Status: 'approved', 'override', 'waived'")


class CapabilityGapResponse(BaseModel):
    id: int
    project_id: int
    investigation_step_id: int
    scientific_requirement: str
    required_input_types: list[dict[str, Any]] | None = None
    required_output_types: list[dict[str, Any]] | None = None
    reason_unavailable: str
    possible_resolution: str
    status: str
    resolution_notes: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CapabilityGapCreate(BaseModel):
    investigation_step_id: int
    scientific_requirement: str = Field(min_length=1)
    required_input_types: list[dict[str, Any]] | None = None
    required_output_types: list[dict[str, Any]] | None = None
    reason_unavailable: str = Field(min_length=1)
    possible_resolution: str = "adapter_development"
    resolution_notes: str | None = None


class CapabilityGapUpdateRequest(BaseModel):
    status: str = Field(description="Status: 'unresolved', 'in_progress', 'resolved', 'waived'")
    possible_resolution: str | None = None
    resolution_notes: str | None = None
    resolved: bool = False


class ScientificApplicationBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    display_name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1)
    host_environment: str = Field(min_length=1, max_length=255)
    invocation_type: str = Field(default="cli_script", max_length=64)
    interface_url: str | None = Field(default=None, max_length=512)
    is_gpu_required: bool = False
    execution_timeout_seconds: int | None = None
    is_enabled: bool = True


class ScientificApplicationCreate(ScientificApplicationBase):
    capabilities: list[ScientificCapabilityCreate] = Field(default_factory=list)


class ScientificApplicationUpdate(BaseModel):
    display_name: str | None = None
    category: str | None = None
    description: str | None = None
    host_environment: str | None = None
    invocation_type: str | None = None
    interface_url: str | None = None
    is_gpu_required: bool | None = None
    execution_timeout_seconds: int | None = None
    is_enabled: bool | None = None


class ScientificApplicationResponse(ScientificApplicationBase):
    id: int
    created_at: datetime
    capabilities: list[ScientificCapabilityResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CapabilityDomainSummaryResponse(BaseModel):
    domain: str
    display_name: str
    description: str
    ebv_dimension: str | None = None
    subdomains: list[str] = Field(default_factory=list)
    total_capabilities: int = 0
    generic_count: int = 0
    identifyshell_count: int = 0
    extension_count: int = 0
    external_count: int = 0


class DomainCoverageSummary(BaseModel):
    domain: str
    display_name: str
    ebv_dimension: str | None = None
    known_specs_count: int = 0
    installed_count: int = 0
    validated_count: int = 0
    extension_count: int = 0
    external_count: int = 0
    gap_count: int = 0


class BiodiversityCoverageMatrixResponse(BaseModel):
    domains: list[DomainCoverageSummary]
    total_known_specs: int
    total_installed: int
    total_validated: int
    total_extensions: int
    total_external: int
    total_gaps: int


class SemanticTypeDefinition(BaseModel):
    type_key: str
    display_name: str
    category: str
    description: str
    recommended_extension: str | None = None
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    identifier_semantics: str = ""
    unit_rules: str = ""
    crs: str | None = None
    missingness_policy: str = ""
    validation_rules: list[str] = Field(default_factory=list)
    sample_structure: dict[str, Any] | None = None
