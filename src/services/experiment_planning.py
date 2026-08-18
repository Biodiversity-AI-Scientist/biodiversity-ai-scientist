import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.llm.contracts import ExperimentPlanningLLMInput, ExperimentPlanningLLMOutput
from src.llm.gateway import LLMGateway
from src.models.analysis_plan import AnalysisPlan
from src.models.investigation_step import InvestigationStep
from src.models.scientific_capability import CapabilitySelection, ScientificCapability
from src.services.scientific_context import ScientificContextService

logger = logging.getLogger(__name__)


class ExperimentPlanningError(Exception):
    pass


class ExperimentPlanningService:
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
                elif "enum" in prop_spec and val not in prop_spec["enum"]:
                    errors.append(f"Parameter '{param_name}' value '{val}' not in allowed values: {prop_spec['enum']}")

            elif expected_type == "boolean":
                if not isinstance(val, bool):
                    errors.append(f"Parameter '{param_name}' must be a boolean, got {type(val).__name__}")

            elif expected_type == "array":
                if not isinstance(val, list):
                    errors.append(f"Parameter '{param_name}' must be a list/array, got {type(val).__name__}")

        return len(errors) == 0, errors

    @classmethod
    def plan_experiment_for_step(
        cls,
        db: Session,
        step_id: int,
        user_guidance: str | None = None,
        llm_gateway: LLMGateway | None = None,
    ) -> AnalysisPlan:
        """
        Executes LLM Stage 4 — Experiment Planning for an InvestigationStep.
        Surrounded by deterministic context assembly and parameter schema validation.
        """
        step = db.get(InvestigationStep, step_id)
        if not step:
            raise ExperimentPlanningError(f"InvestigationStep #{step_id} not found")

        # 1. Deterministic Context Assembly (Phase 7)
        ctx = ScientificContextService.build_experiment_planning_context(
            db=db,
            investigation_step_id=step_id,
        )

        cap_name = ctx.selected_capability.display_name if ctx.selected_capability else "Generic Analytical Method"
        rendered_prompt = ScientificContextService.format_experiment_planning_context_for_prompt(ctx)

        # 2. LLM Gateway Invocation (LLM Stage 4)
        gateway = llm_gateway or LLMGateway()
        payload = ExperimentPlanningLLMInput(
            rendered_context=rendered_prompt,
            step_goal=step.scientific_goal,
            capability_name=cap_name,
            user_guidance=user_guidance,
        )

        try:
            gw_result = gateway.invoke(
                template_id="experiment_planning_v1",
                payload=payload,
            )
            llm_output = ExperimentPlanningLLMOutput.model_validate(gw_result.output)
            meta = gw_result.metadata.model_dump()
        except Exception as e:
            logger.error("LLM experiment planning invocation failed: %s", str(e))
            raise ExperimentPlanningError(f"LLM experiment planning failed: {str(e)}") from e

        # 3. Deterministic Parameter Schema Validation
        param_schema = ctx.parameter_schema
        is_valid, validation_errors = cls.validate_parameters_against_schema(
            parameters=llm_output.parameters,
            schema=param_schema,
        )
        if not is_valid:
            logger.warning("LLM experiment parameter schema warnings: %s", validation_errors)

        # 4. Construct / Update AnalysisPlan (Experiment)
        # Search for existing experiment for this step
        stmt = select(AnalysisPlan).where(
            AnalysisPlan.question_id == step.question_id,
        )
        existing_plans = list(db.scalars(stmt).all())
        matching_plan: AnalysisPlan | None = None
        for p in existing_plans:
            assumptions = p.assumptions or {}
            if assumptions.get("investigation_step_id") == step.id:
                matching_plan = p
                break

        method_name = ctx.selected_capability.capability_key if ctx.selected_capability else step.step_type

        experiment_metadata = {
            "investigation_step_id": step.id,
            "working_title": llm_output.working_title,
            "scientific_objective": llm_output.scientific_objective,
            "selected_dataset_version_id": llm_output.selected_dataset_version_id,
            "selected_artifact_ids": llm_output.selected_artifact_ids,
            "protocol_description": llm_output.protocol_description,
            "parameter_justifications": [j.model_dump() for j in llm_output.parameter_justifications],
            "control_strategy": llm_output.control_strategy,
            "replication_strategy": llm_output.replication_strategy,
            "expected_outputs": llm_output.expected_outputs,
            "completion_criteria": llm_output.completion_criteria,
            "interpretation_criteria": llm_output.interpretation_criteria,
            "known_limitations_and_confounders": llm_output.known_limitations_and_confounders,
            "validation_errors": validation_errors,
            "confidence_score": llm_output.confidence_score,
            "model_provenance": meta,
        }

        if matching_plan:
            matching_plan.estimand = llm_output.scientific_objective
            matching_plan.method = method_name
            matching_plan.parameters = llm_output.parameters
            matching_plan.assumptions = experiment_metadata
            matching_plan.status = "draft"
            matching_plan.dataset_version_id = llm_output.selected_dataset_version_id or ctx.intended_dataset.id if ctx.intended_dataset else None
            plan = matching_plan
        else:
            plan = AnalysisPlan(
                question_id=step.question_id,
                hypothesis_id=ctx.hypothesis.id if ctx.hypothesis else None,
                dataset_version_id=llm_output.selected_dataset_version_id or (ctx.intended_dataset.id if ctx.intended_dataset else None),
                estimand=llm_output.scientific_objective,
                method=method_name,
                parameters=llm_output.parameters,
                assumptions=experiment_metadata,
                exploratory=False,
                status="draft",
            )
            db.add(plan)

        db.commit()
        db.refresh(plan)
        return plan

    @classmethod
    def approve_experiment(
        cls,
        db: Session,
        plan_id: int,
    ) -> AnalysisPlan:
        """
        Transitions an Experiment (AnalysisPlan) from 'draft' or 'proposed' to 'approved' (frozen).
        """
        plan = db.get(AnalysisPlan, plan_id)
        if not plan:
            raise ExperimentPlanningError(f"AnalysisPlan #{plan_id} not found")

        plan.status = "approved"
        db.commit()
        db.refresh(plan)
        return plan

    @classmethod
    def override_parameters(
        cls,
        db: Session,
        plan_id: int,
        parameters: dict[str, Any],
        justification: str | None = None,
    ) -> AnalysisPlan:
        """
        Updates parameters of an experiment with human researcher overrides.
        """
        plan = db.get(AnalysisPlan, plan_id)
        if not plan:
            raise ExperimentPlanningError(f"AnalysisPlan #{plan_id} not found")

        plan.parameters = parameters
        assumptions = dict(plan.assumptions or {})
        if justification:
            assumptions["researcher_override_justification"] = justification
        plan.assumptions = assumptions

        db.commit()
        db.refresh(plan)
        return plan
