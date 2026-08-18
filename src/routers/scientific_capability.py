from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.repositories import scientific_capability as repository
from src.core.contracts.semantic_types import BiodiversityDomain
from src.schemas.scientific_capability import (
    BiodiversityCoverageMatrixResponse,
    CapabilityDomainSummaryResponse,
    CapabilityGapCreate,
    CapabilityGapResponse,
    CapabilityGapUpdateRequest,
    CapabilitySelectionOverrideRequest,
    CapabilitySelectionResponse,
    DomainCoverageSummary,
    ScientificApplicationCreate,
    ScientificApplicationResponse,
    ScientificApplicationUpdate,
    ScientificCapabilityCreate,
    ScientificCapabilityResponse,
    ScientificCapabilityUpdate,
    SemanticTypeDefinition,
)

router = APIRouter(
    tags=["Scientific capabilities & ecosystem inventory"],
)

DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/applications",
    response_model=list[ScientificApplicationResponse],
    summary="List Scientific Applications in the ecosystem",
    description="Retrieve all registered scientific applications, pipelines, and external tools in the ecosystem inventory.",
)
def list_applications_endpoint(
    db: DbSession,
    category: str | None = Query(default=None, description="Filter by category e.g. 'vision_ml', 'embeddings', 'taxonomy', 'statistics', 'dataset'"),
    enabled_only: bool = Query(default=False),
):
    return repository.list_applications(db=db, category=category, enabled_only=enabled_only)


@router.post(
    "/applications",
    response_model=ScientificApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Scientific Application",
    description="Register a new software tool, pipeline, or service in the scientific software inventory.",
)
def create_application_endpoint(
    app_data: ScientificApplicationCreate,
    db: DbSession,
):
    existing = repository.get_application_by_name(db, app_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scientific application with name '{app_data.name}' already exists",
        )
    return repository.create_application(db=db, data=app_data)


@router.get(
    "/applications/{application_id}",
    response_model=ScientificApplicationResponse,
    summary="Read a Scientific Application",
)
def read_application_endpoint(
    application_id: int,
    db: DbSession,
):
    app = repository.get_application(db, application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scientific application not found",
        )
    return app


@router.patch(
    "/applications/{application_id}",
    response_model=ScientificApplicationResponse,
    summary="Update or toggle a Scientific Application",
)
def update_application_endpoint(
    application_id: int,
    app_data: ScientificApplicationUpdate,
    db: DbSession,
):
    app = repository.update_application(db, application_id, app_data)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scientific application not found",
        )
    return app


@router.post(
    "/applications/{application_id}/capabilities",
    response_model=ScientificCapabilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a capability to an existing application",
)
def add_capability_endpoint(
    application_id: int,
    cap_data: ScientificCapabilityCreate,
    db: DbSession,
):
    app = repository.get_application(db, application_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scientific application not found",
        )
    existing_cap = repository.get_capability_by_key(db, cap_data.capability_key)
    if existing_cap:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Capability key '{cap_data.capability_key}' already registered",
        )
    return repository.add_capability_to_application(db, application_id, cap_data)


from src.core.contracts.semantic_types import BIODIVERSITY_DOMAINS, SEMANTIC_DATA_TYPES
from src.schemas.scientific_capability import (
    CapabilityDomainSummaryResponse,
    SemanticTypeDefinition,
)
from src.services.taxonomy_seed import seed_biodiversity_taxonomy


@router.get(
    "/capabilities/domains",
    response_model=list[CapabilityDomainSummaryResponse],
    summary="List Biodiversity Research Domains & Coverage",
    description="Returns the 14 standardized biodiversity research domains, EBV dimensions, and capability count breakdowns.",
)
def list_capability_domains_endpoint(db: DbSession):
    caps = repository.list_capabilities(db=db)
    counts_by_domain: dict[str, dict[str, int]] = {}

    for c in caps:
        dom = c.domain or "biodiversity_informatics"
        if dom not in counts_by_domain:
            counts_by_domain[dom] = {
                "total": 0,
                "generic": 0,
                "identifyshell": 0,
                "extension": 0,
                "external": 0,
            }
        counts_by_domain[dom]["total"] += 1
        scope = getattr(c, "capability_scope", "generic_core")
        if scope == "generic_core":
            counts_by_domain[dom]["generic"] += 1
        elif scope == "identifyshell_specific":
            counts_by_domain[dom]["identifyshell"] += 1
        elif scope == "official_extension":
            counts_by_domain[dom]["extension"] += 1
        elif scope == "external_tool":
            counts_by_domain[dom]["external"] += 1

    summaries = []
    for dom_key, meta in BIODIVERSITY_DOMAINS.items():
        domain_counts = counts_by_domain.get(
            dom_key,
            {"total": 0, "generic": 0, "identifyshell": 0, "extension": 0, "external": 0},
        )
        summaries.append(
            CapabilityDomainSummaryResponse(
                domain=dom_key,
                display_name=meta.display_name,
                description=meta.description,
                ebv_dimension=meta.ebv_dimension.value if meta.ebv_dimension else None,
                subdomains=meta.typical_subdomains,
                total_capabilities=domain_counts["total"],
                generic_count=domain_counts["generic"],
                identifyshell_count=domain_counts["identifyshell"],
                extension_count=domain_counts["extension"],
                external_count=domain_counts["external"],
            )
        )
    return summaries


@router.get(
    "/capabilities/coverage-matrix",
    response_model=BiodiversityCoverageMatrixResponse,
    summary="Biodiversity Capability Coverage Matrix",
    description="Returns domain-by-domain operational status (known specs, installed, validated, extensions, external tools, and gaps).",
)
def get_capability_coverage_matrix_endpoint(db: DbSession):
    caps = repository.list_capabilities(db=db)
    
    # Also fetch open capability gaps grouped by domain if possible
    from src.models import CapabilityGap
    from sqlalchemy import select
    gaps_stmt = select(CapabilityGap).where(CapabilityGap.status.in_(["unresolved", "open", "in_progress"]))
    open_gaps = list(db.scalars(gaps_stmt).all())

    # Map gaps by matching requirement keywords to domain
    domain_gap_counts: dict[str, int] = {d: 0 for d in BIODIVERSITY_DOMAINS.keys()}
    for g in open_gaps:
        req_lower = (g.scientific_requirement or "").lower()
        matched = False
        for d in BIODIVERSITY_DOMAINS.keys():
            if d.replace("_", " ") in req_lower:
                domain_gap_counts[d] += 1
                matched = True
                break
        if not matched:
            domain_gap_counts[BiodiversityDomain.BIODIVERSITY_INFORMATICS.value] += 1

    coverage_by_domain: dict[str, dict[str, int]] = {}
    for dom_key in BIODIVERSITY_DOMAINS.keys():
        coverage_by_domain[dom_key] = {
            "known_specs": 0,
            "installed": 0,
            "validated": 0,
            "extension": 0,
            "external": 0,
        }

    for c in caps:
        dom = c.domain or "biodiversity_informatics"
        if dom not in coverage_by_domain:
            coverage_by_domain[dom] = {"known_specs": 0, "installed": 0, "validated": 0, "extension": 0, "external": 0}
        
        coverage_by_domain[dom]["known_specs"] += 1
        
        # Check implementations or capability-level availability
        impls = getattr(c, "implementations", [])
        has_installed = getattr(c, "availability", "installed") == "installed" or any(getattr(i, "availability", "") == "installed" for i in impls)
        has_external = getattr(c, "availability", "") == "external" or getattr(c, "capability_scope", "") == "external_tool" or any(getattr(i, "availability", "") == "external" for i in impls)
        has_validated = getattr(c, "knowledge_status", "") == "validated" or any(getattr(i, "validation_status", "") == "validated" for i in impls)

        if has_installed:
            coverage_by_domain[dom]["installed"] += 1
        elif has_external:
            coverage_by_domain[dom]["external"] += 1

        if has_validated:
            coverage_by_domain[dom]["validated"] += 1

        scope = getattr(c, "capability_scope", "generic_core")
        if scope == "official_extension":
            coverage_by_domain[dom]["extension"] += 1

    domain_summaries = []
    total_known = 0
    total_installed = 0
    total_validated = 0
    total_extensions = 0
    total_external = 0
    total_gaps = sum(domain_gap_counts.values())

    for dom_key, meta in BIODIVERSITY_DOMAINS.items():
        stats = coverage_by_domain[dom_key]
        gaps = domain_gap_counts.get(dom_key, 0)
        
        total_known += stats["known_specs"]
        total_installed += stats["installed"]
        total_validated += stats["validated"]
        total_extensions += stats["extension"]
        total_external += stats["external"]

        domain_summaries.append(
            DomainCoverageSummary(
                domain=dom_key,
                display_name=meta.display_name,
                ebv_dimension=meta.ebv_dimension.value if meta.ebv_dimension else None,
                known_specs_count=stats["known_specs"],
                installed_count=stats["installed"],
                validated_count=stats["validated"],
                extension_count=stats["extension"],
                external_count=stats["external"],
                gap_count=gaps,
            )
        )

    return BiodiversityCoverageMatrixResponse(
        domains=domain_summaries,
        total_known_specs=total_known,
        total_installed=total_installed,
        total_validated=total_validated,
        total_extensions=total_extensions,
        total_external=total_external,
        total_gaps=total_gaps,
    )


@router.get(
    "/capabilities/semantic-types",
    response_model=list[SemanticTypeDefinition],
    summary="List Biodiversity Semantic Data Types",
    description="Returns the standardized machine-validatable semantic data types catalogue used for scientific input/output contracts.",
)
def list_semantic_types_endpoint():
    types_list = []
    for k, st in SEMANTIC_DATA_TYPES.items():
        types_list.append(
            SemanticTypeDefinition(
                type_key=st.type_key,
                display_name=st.display_name,
                category=st.category,
                description=st.description,
                recommended_extension=st.recommended_extension,
                required_fields=st.required_fields,
                optional_fields=st.optional_fields,
                identifier_semantics=st.identifier_semantics,
                unit_rules=st.unit_rules,
                crs=st.crs,
                missingness_policy=st.missingness_policy,
                validation_rules=st.validation_rules,
                sample_structure=st.sample_structure,
            )
        )
    return types_list


@router.post(
    "/capabilities/seed-taxonomy",
    summary="Seed or update canonical Biodiversity Capability Taxonomy",
    description="Idempotently populates the capability registry with standard biodiversity capabilities and IdentifyShell tools.",
)
def seed_taxonomy_endpoint(db: DbSession):
    return seed_biodiversity_taxonomy(db)


@router.get(
    "/capabilities",
    response_model=list[ScientificCapabilityResponse],
    summary="List Scientific Capabilities",
    description="Retrieve all scientific capabilities across applications with domain, scope, availability, and maturity filters.",
)
def list_capabilities_endpoint(
    db: DbSession,
    domain: str | None = Query(default=None, description="Filter by 14 biodiversity domains e.g. 'species_traits', 'biogeography_macroecology'"),
    scope: str | None = Query(default=None, description="Filter by 4-tier scope: 'generic_core', 'official_extension', 'external_tool', 'identifyshell_specific'"),
    is_generic: bool | None = Query(default=None, description="Filter by generic vs private tool (True/False)"),
    maturity: str | None = Query(default=None, description="Filter by maturity"),
    knowledge_status: str | None = Query(default=None, description="Filter by knowledge status: 'known', 'implemented', 'validated'"),
    availability: str | None = Query(default=None, description="Filter by availability: 'installed', 'not_installed', 'external'"),
    category: str | None = Query(default=None, description="Filter by application category"),
    is_gpu_required: bool | None = Query(default=None),
    enabled_only: bool = Query(default=False),
):
    return repository.list_capabilities(
        db=db,
        category=category,
        domain=domain,
        scope=scope,
        is_generic=is_generic,
        maturity=maturity,
        knowledge_status=knowledge_status,
        availability=availability,
        is_gpu_required=is_gpu_required,
        enabled_only=enabled_only,
    )


@router.get(
    "/capabilities/{capability_id}",
    response_model=ScientificCapabilityResponse,
    summary="Read a Scientific Capability specification",
)
def read_capability_endpoint(
    capability_id: int,
    db: DbSession,
):
    cap = repository.get_capability(db, capability_id)
    if not cap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scientific capability not found",
        )
    return cap


@router.patch(
    "/capabilities/{capability_id}",
    response_model=ScientificCapabilityResponse,
    summary="Update or toggle a Scientific Capability",
)
def update_capability_endpoint(
    capability_id: int,
    cap_data: ScientificCapabilityUpdate,
    db: DbSession,
):
    cap = repository.update_capability(db, capability_id, cap_data)
    if not cap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scientific capability not found",
        )
    return cap


from src.schemas.scientific_capability import (
    CapabilityImplementationCreate,
    CapabilityImplementationResponse,
    CapabilityImplementationUpdate,
)


@router.post(
    "/capabilities/{capability_id}/implementations",
    response_model=CapabilityImplementationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an implementation adapter to a capability",
)
def add_implementation_endpoint(
    capability_id: int,
    impl_data: CapabilityImplementationCreate,
    db: DbSession,
):
    cap = repository.get_capability(db, capability_id)
    if not cap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scientific capability not found",
        )
    return repository.add_implementation_to_capability(db, capability_id, impl_data)


@router.patch(
    "/implementations/{implementation_id}",
    response_model=CapabilityImplementationResponse,
    summary="Update a capability implementation adapter",
)
def update_implementation_endpoint(
    implementation_id: int,
    impl_data: CapabilityImplementationUpdate,
    db: DbSession,
):
    impl = repository.update_implementation(db, implementation_id, impl_data)
    if not impl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Capability implementation not found",
        )
    return impl



# ==============================================================================
# Phase 9: Scientific Capability Matching & Selection Endpoints
# ==============================================================================

from src.schemas.scientific_capability import (
    CapabilityGapResponse,
    CapabilityGapUpdateRequest,
    CapabilitySelectionOverrideRequest,
    CapabilitySelectionResponse,
)
from src.services.capability_selection import CapabilitySelectionService


@router.post(
    "/investigation-steps/{step_id}/capability-selection/match",
    response_model=CapabilitySelectionResponse,
    summary="Match or determine capability for an investigation step",
    description="Runs deterministic eligibility filtering, sole-option auto selection, or LLM comparative selection.",
)
def match_step_capability_endpoint(
    step_id: int,
    db: DbSession,
    user_guidance: str | None = Query(default=None, description="Optional researcher guidance or preferences"),
):
    try:
        return CapabilitySelectionService.match_capability_for_step(
            db=db,
            step_id=step_id,
            user_guidance=user_guidance,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/investigation-steps/{step_id}/capability-selection",
    response_model=CapabilitySelectionResponse | None,
    summary="Get active capability selection for an investigation step",
)
def get_step_capability_selection_endpoint(
    step_id: int,
    db: DbSession,
):
    return CapabilitySelectionService.get_capability_selection_for_step(db=db, step_id=step_id)


@router.put(
    "/investigation-steps/{step_id}/capability-selection/override",
    response_model=CapabilitySelectionResponse,
    summary="Override or manually assign capability selection for an investigation step",
)
def override_step_capability_endpoint(
    step_id: int,
    override_req: CapabilitySelectionOverrideRequest,
    db: DbSession,
):
    try:
        return CapabilitySelectionService.override_capability_selection(
            db=db,
            step_id=step_id,
            override_req=override_req,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/questions/{question_id}/capability-selection/match-all",
    response_model=list[CapabilitySelectionResponse],
    summary="Batch match capabilities for all steps in a question's investigation plan",
)
def match_all_question_capabilities_endpoint(
    question_id: int,
    db: DbSession,
    user_guidance: str | None = Query(default=None),
):
    try:
        return CapabilitySelectionService.match_all_capabilities_for_question(
            db=db,
            question_id=question_id,
            user_guidance=user_guidance,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/projects/{project_id}/capability-gaps",
    response_model=list[CapabilityGapResponse],
    summary="List all capability gaps for a project",
)
def list_project_capability_gaps_endpoint(
    project_id: int,
    db: DbSession,
):
    return CapabilitySelectionService.list_capability_gaps(db=db, project_id=project_id)


@router.patch(
    "/capability-gaps/{gap_id}",
    response_model=CapabilityGapResponse,
    summary="Update resolution state of a capability gap",
)
def update_capability_gap_endpoint(
    gap_id: int,
    update_req: CapabilityGapUpdateRequest,
    db: DbSession,
):
    try:
        return CapabilitySelectionService.update_capability_gap(
            db=db,
            gap_id=gap_id,
            update_req=update_req,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


