"""
Canonical Experiment Domain Service.

This service manages the lifecycle, creation, parameter validation, and AI planning
of Experiments (internally stored in the analysis_plan table).
"""
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.analysis_plan import AnalysisPlan
from src.models.investigation_step import InvestigationStep
from src.models.research_project import ResearchProject
from src.models.research_question import ResearchQuestion
from src.models.scientific_capability import CapabilitySelection, ScientificCapability
from src.llm.contracts import ExperimentPlanningLLMInput, ExperimentPlanningLLMOutput
from src.llm.gateway import LLMGateway
from src.services.scientific_context import ScientificContextService
from src.schemas.experiment import (
    ExperimentCreate,
    ExperimentUpdate,
    ExperimentResponse,
    ExperimentParameterOverrideRequest,
)

logger = logging.getLogger(__name__)


class ExperimentServiceError(Exception):
    """Base exception for Experiment service operations."""


class ExperimentNotFoundError(ExperimentServiceError):
    pass


class ExperimentValidationError(ExperimentServiceError):
    pass


class ExperimentService:
    @classmethod
    def list_experiments_for_project(cls, db: Session, project_id: int) -> list[ExperimentResponse]:
        project = db.get(ResearchProject, project_id)
        if not project:
            raise ExperimentNotFoundError(f"ResearchProject {project_id} not found")
        
        stmt = (
            select(AnalysisPlan)
            .join(ResearchQuestion, AnalysisPlan.question_id == ResearchQuestion.id)
            .where(ResearchQuestion.project_id == project_id)
            .order_by(AnalysisPlan.id.desc())
        )
        plans = db.scalars(stmt).all()
        return [ExperimentResponse.model_validate(p) for p in plans]

    @classmethod
    def list_experiments_for_question(cls, db: Session, question_id: int) -> list[ExperimentResponse]:
        question = db.get(ResearchQuestion, question_id)
        if not question:
            raise ExperimentNotFoundError(f"ResearchQuestion {question_id} not found")

        stmt = (
            select(AnalysisPlan)
            .where(AnalysisPlan.question_id == question_id)
            .order_by(AnalysisPlan.id.desc())
        )
        plans = db.scalars(stmt).all()
        return [ExperimentResponse.model_validate(p) for p in plans]

    @classmethod
    def get_experiment(cls, db: Session, experiment_id: int) -> ExperimentResponse:
        plan = db.get(AnalysisPlan, experiment_id)
        if not plan:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")
        return ExperimentResponse.model_validate(plan)

    @classmethod
    def create_experiment(
        cls,
        db: Session,
        question_id: int,
        data: ExperimentCreate,
    ) -> ExperimentResponse:
        question = db.get(ResearchQuestion, question_id)
        if not question:
            raise ExperimentNotFoundError(f"ResearchQuestion {question_id} not found")

        plan = AnalysisPlan(
            question_id=question_id,
            hypothesis_id=data.hypothesis_id,
            dataset_version_id=data.dataset_version_id,
            estimand=data.estimand,
            method=data.method,
            assumptions=data.assumptions,
            parameters=data.parameters,
            exploratory=data.exploratory,
            status="draft",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return ExperimentResponse.model_validate(plan)

    @classmethod
    def update_experiment(
        cls,
        db: Session,
        experiment_id: int,
        data: ExperimentUpdate,
    ) -> ExperimentResponse:
        plan = db.get(AnalysisPlan, experiment_id)
        if not plan:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")

        if data.estimand is not None:
            plan.estimand = data.estimand
        if data.method is not None:
            plan.method = data.method
        if data.assumptions is not None:
            plan.assumptions = data.assumptions
        if data.parameters is not None:
            plan.parameters = data.parameters
        if data.status is not None:
            plan.status = data.status

        db.commit()
        db.refresh(plan)
        return ExperimentResponse.model_validate(plan)

    @classmethod
    def approve_experiment(cls, db: Session, experiment_id: int) -> ExperimentResponse:
        plan = db.get(AnalysisPlan, experiment_id)
        if not plan:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")

        plan.status = "approved"
        db.commit()
        db.refresh(plan)
        logger.info("Experiment %s approved.", experiment_id)
        return ExperimentResponse.model_validate(plan)

    @classmethod
    def override_parameters(
        cls,
        db: Session,
        experiment_id: int,
        req: ExperimentParameterOverrideRequest,
    ) -> ExperimentResponse:
        plan = db.get(AnalysisPlan, experiment_id)
        if not plan:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")

        plan.parameters = req.parameters
        assumptions = dict(plan.assumptions or {})
        assumptions["researcher_override_justification"] = req.justification or "Manual parameter override"
        assumptions["parameter_override_applied"] = True
        plan.assumptions = assumptions

        db.commit()
        db.refresh(plan)
        return ExperimentResponse.model_validate(plan)

    @staticmethod
    def validate_parameters_against_schema(
        parameters: dict[str, Any],
        schema: dict[str, Any] | None,
    ) -> tuple[bool, list[str]]:
        """
        Deterministically validates pre-specified parameters against a capability's declared JSON input schema.
        """
        if not schema or not isinstance(schema, dict):
            return True, []

        errors: list[str] = []
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        # Check required fields
        for req in required_fields:
            if req not in parameters or parameters[req] is None:
                errors.append(f"Missing required parameter: '{req}'")

        # Check types & constraints
        for param_name, val in parameters.items():
            if param_name not in properties:
                continue

            prop_spec = properties[param_name]
            expected_type = prop_spec.get("type")

            if expected_type == "integer":
                if not isinstance(val, int) or isinstance(val, bool):
                    errors.append(f"Parameter '{param_name}' must be an integer, got {type(val).__name__}")
                else:
                    if "minimum" in prop_spec and val < prop_spec["minimum"]:
                        errors.append(f"Parameter '{param_name}' value {val} is less than minimum {prop_spec['minimum']}")
                    if "maximum" in prop_spec and val > prop_spec["maximum"]:
                        errors.append(f"Parameter '{param_name}' value {val} exceeds maximum {prop_spec['maximum']}")

            elif expected_type == "number":
                if not isinstance(val, (int, float)) or isinstance(val, bool):
                    errors.append(f"Parameter '{param_name}' must be a number, got {type(val).__name__}")
                else:
                    if "minimum" in prop_spec and val < prop_spec["minimum"]:
                        errors.append(f"Parameter '{param_name}' value {val} is less than minimum {prop_spec['minimum']}")
                    if "maximum" in prop_spec and val > prop_spec["maximum"]:
                        errors.append(f"Parameter '{param_name}' value {val} exceeds maximum {prop_spec['maximum']}")

            elif expected_type == "string":
                if not isinstance(val, str):
                    errors.append(f"Parameter '{param_name}' must be a string, got {type(val).__name__}")
                else:
                    if "enum" in prop_spec and val not in prop_spec["enum"]:
                        errors.append(f"Parameter '{param_name}' value '{val}' must be one of {prop_spec['enum']}")

            elif expected_type == "boolean":
                if not isinstance(val, bool):
                    errors.append(f"Parameter '{param_name}' must be a boolean, got {type(val).__name__}")

        return (len(errors) == 0, errors)

    @classmethod
    def plan_experiment_for_step(
        cls,
        db: Session,
        step_id: int,
        user_guidance: str | None = None,
    ) -> ExperimentResponse:
        """
        Phase 10 LLM Stage 4: Experiment Planning.
        """
        from src.services.experiment_planning import ExperimentPlanningService
        plan = ExperimentPlanningService.plan_experiment_for_step(
            db=db,
            step_id=step_id,
            user_guidance=user_guidance,
        )
        return ExperimentResponse.model_validate(plan)

    @classmethod
    def list_experiments_for_step(cls, db: Session, step_id: int) -> list[ExperimentResponse]:
        step = db.get(InvestigationStep, step_id)
        if not step:
            raise ExperimentNotFoundError(f"InvestigationStep {step_id} not found")

        stmt = (
            select(AnalysisPlan)
            .where(AnalysisPlan.question_id == step.question_id)
            .order_by(AnalysisPlan.id.desc())
        )
        all_plans = db.scalars(stmt).all()
        matched = []
        for p in all_plans:
            if isinstance(p.assumptions, dict) and p.assumptions.get("investigation_step_id") == step_id:
                matched.append(p)

        return [ExperimentResponse.model_validate(p) for p in matched]
