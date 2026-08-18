from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class ScientificApplication(Base):
    """
    Physical scientific software, script, pipeline, or external API in the ecosystem.
    Records operational environment, invocation mechanism, GPU needs, and documentation.
    """
    __tablename__ = "scientific_application"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    host_environment: Mapped[str] = mapped_column(String(255), nullable=False)
    invocation_type: Mapped[str] = mapped_column(String(64), nullable=False, default="cli_script")
    interface_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_gpu_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    execution_timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    capabilities: Mapped[list["ScientificCapability"]] = relationship(
        "ScientificCapability",
        back_populates="application",
        cascade="all, delete-orphan",
    )


class ScientificCapability(Base):
    """
    A discrete scientific capability/operation exposed by a ScientificApplication.
    Defines scientific purpose, input/output schemas, parameter contracts, and AnalysisRun linkage.
    """
    __tablename__ = "scientific_capability"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("scientific_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    capability_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scientific_purpose: Mapped[str] = mapped_column(Text, nullable=False)
    scientific_tasks: Mapped[str | None] = mapped_column(Text, nullable=True)
    typical_duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reproducibility_level: Mapped[str] = mapped_column(String(64), nullable=False, default="deterministic")
    modifies_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    creates_result: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creates_artifact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creates_dataset_version: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False, default="biodiversity_informatics", index=True)
    subdomain: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ebv_dimension: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capability_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="generic_core", index=True)
    is_generic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scientific_maturity: Mapped[str] = mapped_column(String(32), nullable=False, default="installed")
    knowledge_status: Mapped[str] = mapped_column(String(32), nullable=False, default="known")
    availability: Mapped[str] = mapped_column(String(32), nullable=False, default="installed")
    expected_evidence_types: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    preconditions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    scientific_assumptions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    scientific_constraints: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    input_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    output_schema: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    input_types: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    output_types: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    default_parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    application: Mapped["ScientificApplication"] = relationship(
        "ScientificApplication",
        back_populates="capabilities",
    )
    implementations: Mapped[list["CapabilityImplementation"]] = relationship(
        "CapabilityImplementation",
        back_populates="capability",
        cascade="all, delete-orphan",
    )


class CapabilityImplementation(Base):
    """
    Concrete software adapter, container, pipeline, or service implementation that executes a ScientificCapability.
    Supports a 1:N relationship where one generic scientific capability maps to 0..N concrete implementations.
    """
    __tablename__ = "capability_implementation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scientific_capability_id: Mapped[int] = mapped_column(
        ForeignKey("scientific_capability.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    implementation_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False, default="core_engine")
    adapter_module: Mapped[str | None] = mapped_column(String(255), nullable=True)
    backend_environment: Mapped[str] = mapped_column(String(100), nullable=False, default="local_host")
    runtime_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    implementation_scope: Mapped[str] = mapped_column(String(64), nullable=False, default="generic_core")
    availability: Mapped[str] = mapped_column(String(32), nullable=False, default="installed")
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="known")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    execution_parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    capability: Mapped["ScientificCapability"] = relationship(
        "ScientificCapability",
        back_populates="implementations",
    )


class CapabilitySelection(Base):
    """
    Records the mapping and selection rationale between an InvestigationStep and a ScientificCapability.
    Persists eligible candidates, selection method, scientific rationale, and rejected alternatives.
    """
    __tablename__ = "capability_selection"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    investigation_step_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_step.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    selected_capability_id: Mapped[int | None] = mapped_column(
        ForeignKey("scientific_capability.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    eligible_capability_ids: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    selection_method: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="deterministic_sole_option",
    )  # deterministic_sole_option, llm_comparative_selection, manual_researcher_selection, none_adequate
    scientific_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejected_alternatives: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    known_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    researcher_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="proposed",
    )  # proposed, approved, override, waived
    llm_provenance: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    step: Mapped["InvestigationStep"] = relationship(
        "InvestigationStep",
        foreign_keys=[investigation_step_id],
    )
    selected_capability: Mapped["ScientificCapability | None"] = relationship(
        "ScientificCapability",
        foreign_keys=[selected_capability_id],
    )


class CapabilityGap(Base):
    """
    Represents scientifically required functionality that the system cannot currently perform adequately.
    Prevents hallucinated execution and drives adapter development or manual import.
    """
    __tablename__ = "capability_gap"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    investigation_step_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_step.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scientific_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    required_input_types: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    required_output_types: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    reason_unavailable: Mapped[str] = mapped_column(Text, nullable=False)
    possible_resolution: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="adapter_development",
    )  # adapter_development, external_manual_import, plan_revision
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unresolved",
    )  # unresolved, in_progress, resolved, waived
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project: Mapped["ResearchProject"] = relationship(
        "ResearchProject",
        foreign_keys=[project_id],
    )
    step: Mapped["InvestigationStep"] = relationship(
        "InvestigationStep",
        foreign_keys=[investigation_step_id],
    )

