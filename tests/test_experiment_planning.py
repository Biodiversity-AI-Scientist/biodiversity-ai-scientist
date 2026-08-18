import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.database import SessionLocal
from src.llm.contracts import GatewayResult, InvocationMetadata
from src.main import app
from src.models import (
    AnalysisPlan,
    DatasetVersion,
    InvestigationPlanGeneration,
    InvestigationStep,
    ResearchProject,
    ResearchQuestion,
    ScientificApplication,
    ScientificCapability,
)
from src.models.scientific_capability import CapabilitySelection
from src.repositories import research_project as project_repo
from src.services.experiment_planning import ExperimentPlanningService


class TestExperimentPlanning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.client = TestClient(app)

        # Create test research project
        cls.project = ResearchProject(
            title=f"Test Nassarius Phase 10 Project {int(datetime.now(timezone.utc).timestamp())}",
            objective="Testing Phase 10 Experiment Planning",
            status="active",
        )
        cls.db.add(cls.project)
        cls.db.flush()

        cls.question = ResearchQuestion(
            project_id=cls.project.id,
            question="Does apertural dentition correlate with geographic habitat in Nassarius?",
            status="open",
        )
        cls.db.add(cls.question)
        cls.db.flush()

        cls.dataset = DatasetVersion(
            project_id=cls.project.id,
            version_key=f"v1.0-test-{int(datetime.now(timezone.utc).timestamp())}",
            source_system="gbif",
            member_count=150,
        )
        cls.db.add(cls.dataset)
        cls.db.flush()

        # Scientific Application & Capability with strict schema
        cls.app_record = ScientificApplication(
            name=f"permanova_tool_{int(datetime.now(timezone.utc).timestamp())}",
            display_name="PERMANOVA Morphological Association",
            description="PERMANOVA statistical test application",
            category="statistical_analysis",
            host_environment="server_110",
            invocation_type="python_callable",
            is_gpu_required=False,
            is_enabled=True,
        )
        cls.db.add(cls.app_record)
        cls.db.flush()

        cls.capability = ScientificCapability(
            application_id=cls.app_record.id,
            capability_key=f"permanova_analysis_{int(datetime.now(timezone.utc).timestamp())}",
            display_name="Multivariate PERMANOVA",
            scientific_purpose="Tests morphological clustering association with geographic region.",
            scientific_tasks="statistical_analysis",
            input_types=[{"semantic_type": "image_dataset_v1", "mime_type": "application/x-parquet"}],
            output_types=[{"semantic_type": "statistical_summary_v1", "mime_type": "application/json"}],
            input_schema={
                "type": "object",
                "required": ["permutations", "distance_metric"],
                "properties": {
                    "permutations": {"type": "integer", "minimum": 99, "maximum": 9999},
                    "distance_metric": {"type": "string", "enum": ["bray_curtis", "euclidean", "cosine"]},
                    "random_seed": {"type": "integer", "minimum": 1},
                },
            },
            reproducibility_level="deterministic_with_seed",
            is_enabled=True,
        )
        cls.db.add(cls.capability)
        cls.db.flush()

        # Generation & Step
        cls.gen = InvestigationPlanGeneration(
            project_id=cls.project.id,
            question_id=cls.question.id,
            summary_rationale="Decomposition for Phase 10",
            identified_uncertainties=[],
            context_summary={},
            model_provenance={},
        )
        cls.db.add(cls.gen)
        cls.db.flush()

        cls.step = InvestigationStep(
            project_id=cls.project.id,
            question_id=cls.question.id,
            generation_id=cls.gen.id,
            title="Statistical association testing",
            scientific_goal="Assess whether geographic region is significantly associated with shell morphology",
            rationale="Quantify population structure",
            step_type="statistical_analysis",
            requires_capability=True,
            requires_experiment=True,
            required_operation="permanova",
            expected_evidence="p-value and pseudo-F statistic",
            completion_criteria="p-value < 0.05",
            status="pending",
            display_order=1,
        )
        cls.db.add(cls.step)
        cls.db.flush()

        # Capability Selection
        cls.selection = CapabilitySelection(
            investigation_step_id=cls.step.id,
            selected_capability_id=cls.capability.id,
            selection_method="deterministic_sole_option",
            scientific_rationale="PERMANOVA is the standard test for non-parametric distance matrices.",
            rejected_alternatives=[],
            known_limitations=None,
            researcher_status="approved",
        )
        cls.db.add(cls.selection)
        cls.db.commit()

        # Mock LLMGateway
        cls.patcher = patch("src.llm.gateway.LLMGateway.invoke")
        cls.mock_invoke = cls.patcher.start()
        cls.mock_invoke.return_value = GatewayResult(
            output={
                "working_title": "PERMANOVA Morphological Association Test",
                "scientific_objective": "Test whether shell morphology differs significantly between Saldanha Bay and Algoa Bay.",
                "selected_dataset_version_id": cls.dataset.id,
                "selected_artifact_ids": [],
                "protocol_description": "Compute pairwise Euclidean distances over DINOv3 features, then run PERMANOVA with 999 permutations.",
                "parameters": {
                    "permutations": 999,
                    "distance_metric": "euclidean",
                    "random_seed": 42,
                },
                "parameter_justifications": [
                    {"parameter_name": "permutations", "value": 999, "scientific_justification": "Standard permutation depth for p < 0.001 precision."},
                    {"parameter_name": "distance_metric", "value": "euclidean", "scientific_justification": "Appropriate for continuous normalized DINOv3 embeddings."},
                    {"parameter_name": "random_seed", "value": 42, "scientific_justification": "Fixed seed for deterministic reproducibility."},
                ],
                "control_strategy": "Provider-adjusted stratified permutation to account for imaging protocol differences.",
                "replication_strategy": "10-fold repeated permutation test.",
                "expected_outputs": ["pseudo_F_statistic", "empirical_p_value", "pcoa_ordination_plot"],
                "completion_criteria": "Completion of 999 permutations with non-null p-value.",
                "interpretation_criteria": "p < 0.01 supports significant morphological divergence; p >= 0.05 indicates panmictic variation.",
                "known_limitations_and_confounders": ["Uneven specimen sample sizes between northern and southern bays."],
                "confidence_score": 0.95,
            },
            metadata=InvocationMetadata(
                invocation_id="test-p10-inv",
                provider="mock",
                model="gemini-2.5-flash",
                template_id="experiment_planning_v1",
                schema_id="experiment_planning_v1",
                provider_request_id="req-p10",
                provider_status="success",
                attempts=1,
                latency_ms=15,
                input_tokens=150,
                output_tokens=100,
                prompt_sha256="sha123",
                response_sha256="sha456",
            ),
        )

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        project_repo.archive_project(cls.db, cls.project.id)
        project_repo.delete_project(cls.db, cls.project.id)
        cls.db.delete(cls.capability)
        cls.db.delete(cls.app_record)
        cls.db.commit()
        cls.db.close()

    def test_01_parameter_schema_validation(self):
        schema = self.capability.input_schema
        # Valid parameters
        valid_params = {"permutations": 999, "distance_metric": "euclidean", "random_seed": 42}
        is_valid, errors = ExperimentPlanningService.validate_parameters_against_schema(valid_params, schema)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Missing required parameter
        invalid_params = {"distance_metric": "euclidean"}
        is_valid, errors = ExperimentPlanningService.validate_parameters_against_schema(invalid_params, schema)
        self.assertFalse(is_valid)
        self.assertTrue(any("permutations" in e for e in errors))

        # Invalid enum
        invalid_enum = {"permutations": 999, "distance_metric": "manhattan"}
        is_valid, errors = ExperimentPlanningService.validate_parameters_against_schema(invalid_enum, schema)
        self.assertFalse(is_valid)
        self.assertTrue(any("allowed values" in e for e in errors))

    def test_02_plan_experiment_for_step(self):
        plan = ExperimentPlanningService.plan_experiment_for_step(
            db=self.db,
            step_id=self.step.id,
            user_guidance="Focus on Saldanha Bay vs Algoa Bay",
        )
        self.assertIsNotNone(plan)
        self.assertEqual(plan.status, "draft")
        self.assertEqual(plan.parameters["permutations"], 999)
        self.assertEqual(plan.parameters["distance_metric"], "euclidean")
        self.assertIn("interpretation_criteria", plan.assumptions)
        self.assertEqual(plan.assumptions["investigation_step_id"], self.step.id)

    def test_03_approve_experiment(self):
        # Retrieve planned experiment
        plan = self.db.query(AnalysisPlan).filter(AnalysisPlan.question_id == self.question.id).first()
        self.assertIsNotNone(plan)

        approved = ExperimentPlanningService.approve_experiment(self.db, plan.id)
        self.assertEqual(approved.status, "approved")

    def test_04_override_parameters(self):
        plan = self.db.query(AnalysisPlan).filter(AnalysisPlan.question_id == self.question.id).first()
        updated = ExperimentPlanningService.override_parameters(
            db=self.db,
            plan_id=plan.id,
            parameters={"permutations": 4999, "distance_metric": "bray_curtis", "random_seed": 101},
            justification="Increased permutation count for publication-grade precision.",
        )
        self.assertEqual(updated.parameters["permutations"], 4999)
        self.assertEqual(updated.assumptions["researcher_override_justification"], "Increased permutation count for publication-grade precision.")

    def test_05_rest_api_endpoints(self):
        # 1. Plan experiment via API
        resp = self.client.post(
            f"/investigation-steps/{self.step.id}/experiments/plan",
            json={"user_guidance": "Include provider adjustment"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        plan_id = data["id"]
        self.assertEqual(data["status"], "draft")

        # 2. List experiments for step
        resp = self.client.get(f"/investigation-steps/{self.step.id}/experiments")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.json()) >= 1)

        # 3. Override parameters via API
        resp = self.client.put(
            f"/analysis-plans/{plan_id}/parameters",
            json={
                "parameters": {"permutations": 1999, "distance_metric": "cosine"},
                "justification": "Testing cosine metric",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["parameters"]["permutations"], 1999)

        # 4. Approve via API
        resp = self.client.post(f"/analysis-plans/{plan_id}/approve")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "approved")


if __name__ == "__main__":
    unittest.main()
