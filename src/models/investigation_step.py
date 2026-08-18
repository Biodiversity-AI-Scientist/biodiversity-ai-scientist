from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class InvestigationPlanGeneration(Base):
    __tablename__ = "investigation_plan_generation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("research_question.id"),
        nullable=False,
        index=True,
    )

    research_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_plan.id"),
        nullable=True,
        index=True,
    )

    summary_rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    identified_uncertainties: Mapped[list[Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    model_provenance: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    context_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    project = relationship("ResearchProject")
    question = relationship("ResearchQuestion")
    research_plan = relationship("ResearchPlan")
    steps: Mapped[list["InvestigationStep"]] = relationship(
        "InvestigationStep",
        back_populates="generation",
        cascade="all, delete-orphan",
    )


class InvestigationStep(Base):
    __tablename__ = "investigation_step"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("research_project.id"),
        nullable=False,
        index=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("research_question.id"),
        nullable=False,
        index=True,
    )

    research_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_plan.id"),
        nullable=True,
        index=True,
    )

    generation_id: Mapped[int | None] = mapped_column(
        ForeignKey("investigation_plan_generation.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    scientific_goal: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    step_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    requires_capability: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    requires_experiment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    required_operation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expected_evidence: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    completion_criteria: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="proposed",
        index=True,
    )

    researcher_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    project = relationship("ResearchProject")
    question = relationship("ResearchQuestion")
    research_plan = relationship("ResearchPlan")
    generation = relationship("InvestigationPlanGeneration", back_populates="steps")

    dependencies: Mapped[list["InvestigationStepDependency"]] = relationship(
        "InvestigationStepDependency",
        foreign_keys="[InvestigationStepDependency.step_id]",
        cascade="all, delete-orphan",
        back_populates="step",
    )

    dependents: Mapped[list["InvestigationStepDependency"]] = relationship(
        "InvestigationStepDependency",
        foreign_keys="[InvestigationStepDependency.depends_on_step_id]",
        cascade="all, delete-orphan",
        back_populates="depends_on_step",
    )


class InvestigationStepDependency(Base):
    __tablename__ = "investigation_step_dependency"
    __table_args__ = (
        UniqueConstraint("step_id", "depends_on_step_id", name="uq_step_dependency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    step_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_step.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    depends_on_step_id: Mapped[int] = mapped_column(
        ForeignKey("investigation_step.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    step = relationship("InvestigationStep", foreign_keys=[step_id], back_populates="dependencies")
    depends_on_step = relationship("InvestigationStep", foreign_keys=[depends_on_step_id], back_populates="dependents")
