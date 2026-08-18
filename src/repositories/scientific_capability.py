from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.models.scientific_capability import (
    CapabilityImplementation,
    ScientificApplication,
    ScientificCapability,
)
from src.schemas.scientific_capability import (
    CapabilityImplementationCreate,
    CapabilityImplementationUpdate,
    ScientificApplicationCreate,
    ScientificApplicationUpdate,
    ScientificCapabilityCreate,
    ScientificCapabilityUpdate,
)



def list_applications(
    db: Session,
    category: str | None = None,
    enabled_only: bool = False,
) -> list[ScientificApplication]:
    stmt = (
        select(ScientificApplication)
        .options(
            selectinload(ScientificApplication.capabilities).selectinload(ScientificCapability.implementations)
        )
        .order_by(ScientificApplication.id)
    )
    if category:
        stmt = stmt.where(ScientificApplication.category == category)
    if enabled_only:
        stmt = stmt.where(ScientificApplication.is_enabled.is_(True))

    return list(db.scalars(stmt).all())


def get_application(
    db: Session,
    application_id: int,
) -> ScientificApplication | None:
    stmt = (
        select(ScientificApplication)
        .options(
            selectinload(ScientificApplication.capabilities).selectinload(ScientificCapability.implementations)
        )
        .where(ScientificApplication.id == application_id)
    )
    return db.scalars(stmt).first()


def get_application_by_name(
    db: Session,
    name: str,
) -> ScientificApplication | None:
    stmt = (
        select(ScientificApplication)
        .options(
            selectinload(ScientificApplication.capabilities).selectinload(ScientificCapability.implementations)
        )
        .where(ScientificApplication.name == name)
    )
    return db.scalars(stmt).first()


def create_application(
    db: Session,
    data: ScientificApplicationCreate,
) -> ScientificApplication:
    app = ScientificApplication(
        name=data.name,
        display_name=data.display_name,
        category=data.category,
        description=data.description,
        host_environment=data.host_environment,
        invocation_type=data.invocation_type,
        interface_url=data.interface_url,
        is_gpu_required=data.is_gpu_required,
        execution_timeout_seconds=data.execution_timeout_seconds,
        is_enabled=data.is_enabled,
    )
    db.add(app)
    db.flush()

    for cap_data in data.capabilities:
        cap = ScientificCapability(
            application_id=app.id,
            capability_key=cap_data.capability_key,
            display_name=cap_data.display_name,
            scientific_purpose=cap_data.scientific_purpose,
            domain=getattr(cap_data, "domain", "biodiversity_informatics"),
            subdomain=getattr(cap_data, "subdomain", None),
            ebv_dimension=getattr(cap_data, "ebv_dimension", None),
            capability_scope=getattr(cap_data, "capability_scope", "generic_core"),
            is_generic=getattr(cap_data, "is_generic", True),
            scientific_maturity=getattr(cap_data, "scientific_maturity", "installed"),
            knowledge_status=getattr(cap_data, "knowledge_status", "known"),
            availability=getattr(cap_data, "availability", "installed"),
            expected_evidence_types=getattr(cap_data, "expected_evidence_types", None),
            preconditions=getattr(cap_data, "preconditions", None),
            scientific_assumptions=getattr(cap_data, "scientific_assumptions", None),
            scientific_constraints=getattr(cap_data, "scientific_constraints", None),
            scientific_tasks=cap_data.scientific_tasks,
            typical_duration=cap_data.typical_duration,
            reproducibility_level=cap_data.reproducibility_level,
            modifies_data=cap_data.modifies_data,
            creates_result=cap_data.creates_result,
            creates_artifact=cap_data.creates_artifact,
            input_schema=cap_data.input_schema,
            output_schema=cap_data.output_schema,
            input_types=cap_data.input_types,
            output_types=cap_data.output_types,
            default_parameters=cap_data.default_parameters,
            is_enabled=cap_data.is_enabled,
        )
        db.add(cap)
        db.flush()

        for impl_data in getattr(cap_data, "implementations", []):
            impl = CapabilityImplementation(
                scientific_capability_id=cap.id,
                implementation_key=impl_data.implementation_key,
                display_name=impl_data.display_name,
                provider=impl_data.provider,
                adapter_module=impl_data.adapter_module,
                backend_environment=impl_data.backend_environment,
                runtime_version=impl_data.runtime_version,
                availability=impl_data.availability,
                validation_status=impl_data.validation_status,
                is_default=impl_data.is_default,
                execution_parameters=impl_data.execution_parameters,
            )
            db.add(impl)

    db.commit()
    db.refresh(app)
    return app


def list_capabilities(
    db: Session,
    category: str | None = None,
    domain: str | None = None,
    scope: str | None = None,
    is_generic: bool | None = None,
    maturity: str | None = None,
    knowledge_status: str | None = None,
    availability: str | None = None,
    is_gpu_required: bool | None = None,
    enabled_only: bool = False,
) -> list[ScientificCapability]:
    stmt = (
        select(ScientificCapability)
        .join(ScientificApplication, ScientificCapability.application_id == ScientificApplication.id)
        .options(
            selectinload(ScientificCapability.application),
            selectinload(ScientificCapability.implementations),
        )
        .order_by(ScientificCapability.id)
    )
    if category:
        stmt = stmt.where(ScientificApplication.category == category)
    if domain:
        stmt = stmt.where(ScientificCapability.domain == domain)
    if scope:
        stmt = stmt.where(ScientificCapability.capability_scope == scope)
    if is_generic is not None:
        stmt = stmt.where(ScientificCapability.is_generic == is_generic)
    if maturity:
        stmt = stmt.where(ScientificCapability.scientific_maturity == maturity)
    if knowledge_status:
        stmt = stmt.where(ScientificCapability.knowledge_status == knowledge_status)
    if availability:
        stmt = stmt.where(
            (ScientificCapability.availability == availability) |
            (ScientificCapability.implementations.any(CapabilityImplementation.availability == availability))
        )
    if is_gpu_required is not None:
        stmt = stmt.where(ScientificApplication.is_gpu_required == is_gpu_required)
    if enabled_only:
        stmt = stmt.where(ScientificCapability.is_enabled.is_(True))

    return list(db.scalars(stmt).all())


def get_capability(
    db: Session,
    capability_id: int,
) -> ScientificCapability | None:
    stmt = (
        select(ScientificCapability)
        .options(
            selectinload(ScientificCapability.application),
            selectinload(ScientificCapability.implementations),
        )
        .where(ScientificCapability.id == capability_id)
    )
    return db.scalars(stmt).first()


def get_capability_by_key(
    db: Session,
    capability_key: str,
) -> ScientificCapability | None:
    stmt = (
        select(ScientificCapability)
        .options(
            selectinload(ScientificCapability.application),
            selectinload(ScientificCapability.implementations),
        )
        .where(ScientificCapability.capability_key == capability_key)
    )
    return db.scalars(stmt).first()


def add_capability_to_application(
    db: Session,
    application_id: int,
    data: ScientificCapabilityCreate,
) -> ScientificCapability:
    cap = ScientificCapability(
        application_id=application_id,
        capability_key=data.capability_key,
        display_name=data.display_name,
        scientific_purpose=data.scientific_purpose,
        domain=data.domain,
        subdomain=data.subdomain,
        ebv_dimension=data.ebv_dimension,
        capability_scope=data.capability_scope,
        is_generic=data.is_generic,
        scientific_maturity=data.scientific_maturity,
        knowledge_status=data.knowledge_status,
        availability=data.availability,
        expected_evidence_types=data.expected_evidence_types,
        preconditions=data.preconditions,
        scientific_assumptions=data.scientific_assumptions,
        scientific_constraints=data.scientific_constraints,
        scientific_tasks=data.scientific_tasks,
        typical_duration=data.typical_duration,
        reproducibility_level=data.reproducibility_level,
        modifies_data=data.modifies_data,
        creates_result=data.creates_result,
        creates_artifact=data.creates_artifact,
        input_schema=data.input_schema,
        output_schema=data.output_schema,
        input_types=data.input_types,
        output_types=data.output_types,
        default_parameters=data.default_parameters,
        is_enabled=data.is_enabled,
    )
    db.add(cap)
    db.flush()

    for impl_data in getattr(data, "implementations", []):
        impl = CapabilityImplementation(
            scientific_capability_id=cap.id,
            implementation_key=impl_data.implementation_key,
            display_name=impl_data.display_name,
            provider=impl_data.provider,
            adapter_module=impl_data.adapter_module,
            backend_environment=impl_data.backend_environment,
            runtime_version=impl_data.runtime_version,
            availability=impl_data.availability,
            validation_status=impl_data.validation_status,
            is_default=impl_data.is_default,
            execution_parameters=impl_data.execution_parameters,
        )
        db.add(impl)

    db.commit()
    db.refresh(cap)
    return cap


def add_implementation_to_capability(
    db: Session,
    capability_id: int,
    data: CapabilityImplementationCreate,
) -> CapabilityImplementation:
    impl = CapabilityImplementation(
        scientific_capability_id=capability_id,
        implementation_key=data.implementation_key,
        display_name=data.display_name,
        provider=data.provider,
        adapter_module=data.adapter_module,
        backend_environment=data.backend_environment,
        runtime_version=data.runtime_version,
        availability=data.availability,
        validation_status=data.validation_status,
        is_default=data.is_default,
        execution_parameters=data.execution_parameters,
    )
    db.add(impl)
    db.commit()
    db.refresh(impl)
    return impl


def update_application(
    db: Session,
    application_id: int,
    data: "ScientificApplicationUpdate",
) -> ScientificApplication | None:
    app = get_application(db, application_id)
    if not app:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(app, field, value)
    db.commit()
    db.refresh(app)
    return app


def update_capability(
    db: Session,
    capability_id: int,
    data: ScientificCapabilityUpdate,
) -> ScientificCapability | None:
    cap = get_capability(db, capability_id)
    if not cap:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cap, field, value)
    db.commit()
    db.refresh(cap)
    return cap


def get_implementation(
    db: Session,
    implementation_id: int,
) -> CapabilityImplementation | None:
    stmt = select(CapabilityImplementation).where(CapabilityImplementation.id == implementation_id)
    return db.scalars(stmt).first()


def update_implementation(
    db: Session,
    implementation_id: int,
    data: CapabilityImplementationUpdate,
) -> CapabilityImplementation | None:
    impl = get_implementation(db, implementation_id)
    if not impl:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(impl, field, value)
    db.commit()
    db.refresh(impl)
    return impl

