import unittest
from fastapi.testclient import TestClient

from src.main import app
from src.database import SessionLocal
from src.models import (
    AnalysisPlan,
    AnalysisRun,
    Artifact,
    Claim,
    DatasetVersion,
    Decision,
    EvidenceItem,
    Hypothesis,
    Prediction,
    ResearchPlan,
    ResearchProject,
    ResearchQuestion,
    Result,
    Review,
    ScientificApplication,
    ScientificCapability,
)
from src.schemas.scientific_context import (
    CapabilityMatchingContext,
    ExperimentPlanningContext,
    InvestigationPlanningContext,
    ResultInterpretationContext,
    ScientificContextType,
)
from src.services.context import build_brainstorming_context
from src.services.scientific_context import ScientificContextService


class TestScientificContextService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.client = TestClient(app)

        # Setup isolated scientific project fixture
        cls.project = ResearchProject(
            title="Scientific Context Test Project",
            objective="Testing generalized scientific context generation",
        )
        cls.db.add(cls.project)

        cls.db.flush()

        # Research Plans (Draft v1 and Approved v2)
        cls.plan_v1 = ResearchPlan(
            project_id=cls.project.id,
            version=1,
            title="Old Draft Plan",
            status="draft",
            content={"objective": "Preliminary exploration"},
        )
        cls.plan_v2_approved = ResearchPlan(
            project_id=cls.project.id,
            version=2,
            title="Approved Geographic Variation Plan",
            status="approved",
            content={
                "objective": "Determine whether morphological variation in shell outline correlates with geographic basin.",
                "scientific_background": "Nassarius populations exhibit phenotypic disparity across oceanic zones.",
                "primary_research_question": "Does shell shape differ between Atlantic and Indo-Pacific populations?",
                "evidence_required": ["2D shell coordinates", "Geographic coordinates"],
                "important_confounders": ["Depth gradient", "Substrate type"],
                "sources_of_bias": ["Museum sampling density"],
                "interpretation_criteria": "Reject H0 if PERMANOVA p < 0.01",
            },
        )
        cls.db.add_all([cls.plan_v1, cls.plan_v2_approved])
        cls.db.flush()

        # Focal Research Question Q1
        cls.q1 = ResearchQuestion(
            project_id=cls.project.id,
            question="Does shell shape differ significantly between Atlantic and Indo-Pacific populations?",
            status="open",
            inferential_level="confirmatory",
        )
        # Unrelated Research Question Q2
        cls.q2 = ResearchQuestion(
            project_id=cls.project.id,
            question="What is the mutation rate of mitochondrial COX1 in Nassarius?",
            status="open",
            inferential_level="exploratory",
        )
        cls.db.add_all([cls.q1, cls.q2])
        cls.db.flush()

        # Hypotheses
        cls.h1_q1 = Hypothesis(
            question_id=cls.q1.id,
            statement="Atlantic populations have higher spire aspect ratios than Indo-Pacific populations.",
            status="active",
            rationale="Colder water temperatures select for elongated shell spires.",
        )
        cls.h2_q2 = Hypothesis(
            question_id=cls.q2.id,
            statement="COX1 mutation rate exceeds 2% per million years in tropical gastropods.",
            status="active",
        )
        cls.db.add_all([cls.h1_q1, cls.h2_q2])
        cls.db.flush()

        # Prediction for H1
        cls.p1 = Prediction(
            hypothesis_id=cls.h1_q1.id,
            statement="PCA component 1 will separate Atlantic specimens from Indo-Pacific specimens with >80% accuracy.",
        )
        cls.db.add(cls.p1)

        # Dataset Version
        cls.dataset = DatasetVersion(
            project_id=cls.project.id,
            version_key="TEST_DSV_01",
            source_system="NFS_TEST",
            member_count=450,
            grouping_keys=["specimen_id", "locality"],
            manifest_sha256="abc123def4567890",
        )
        cls.db.add(cls.dataset)
        cls.db.flush()

        # Experiment (AnalysisPlan) & Run for Q1
        cls.plan_q1 = AnalysisPlan(
            question_id=cls.q1.id,
            hypothesis_id=cls.h1_q1.id,
            dataset_version_id=cls.dataset.id,
            method="Multivariate PCA & PERMANOVA",
            estimand="Centroid distance between regional groups",
            status="completed",
        )
        cls.db.add(cls.plan_q1)
        cls.db.flush()

        cls.run_q1 = AnalysisRun(
            analysis_plan_id=cls.plan_q1.id,
            dataset_version_id=cls.dataset.id,
            status="completed",
            parameters={"n_components": 3, "permutations": 999},
        )
        cls.db.add(cls.run_q1)
        cls.db.flush()

        # Result for Q1
        cls.res_q1 = Result(
            analysis_run_id=cls.run_q1.id,
            result_type="permanova_output",
            summary="PERMANOVA F=14.2, p=0.001 indicating significant regional morphological distinction.",
            payload={"f_stat": 14.2, "p_value": 0.001},
        )
        cls.db.add(cls.res_q1)

        # Decision & Claim for Q1
        cls.decision = Decision(
            project_id=cls.project.id,
            question_id=cls.q1.id,
            decision_type="methodology_choice",
            outcome="use_procrustes_morphometrics",
            rationale="Linear measurements were insufficient to capture aperture curve.",
        )
        cls.claim = Claim(
            project_id=cls.project.id,
            question_id=cls.q1.id,
            text="Geographic isolation drives shell elongation in Atlantic Nassarius.",
            claim_type="empirical_inference",
            epistemic_status="supported_by_data",
        )
        cls.test_app = ScientificApplication(
            name="test_vision_ml_suite",
            display_name="Test Vision ML Suite",
            category="vision_ml",
            description="Testing capability context",
            host_environment="local",
            is_enabled=True,
        )
        cls.db.add(cls.test_app)
        cls.db.flush()

        cls.test_cap = ScientificCapability(
            application_id=cls.test_app.id,
            capability_key="extract_foundation_visual_embeddings",
            display_name="Extract Foundation Visual Embeddings",
            scientific_purpose="Extract dense embeddings",
            is_enabled=True,
        )
        cls.db.add(cls.test_cap)
        cls.db.add_all([cls.decision, cls.claim])
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up test records
        cls.db.query(ScientificCapability).filter(ScientificCapability.id == cls.test_cap.id).delete()
        cls.db.query(ScientificApplication).filter(ScientificApplication.id == cls.test_app.id).delete()
        cls.db.query(Result).filter(Result.analysis_run_id == cls.run_q1.id).delete()
        cls.db.query(AnalysisRun).filter(AnalysisRun.id == cls.run_q1.id).delete()
        cls.db.query(AnalysisPlan).filter(AnalysisPlan.id == cls.plan_q1.id).delete()
        cls.db.query(Decision).filter(Decision.id == cls.decision.id).delete()
        cls.db.query(Claim).filter(Claim.id == cls.claim.id).delete()
        cls.db.query(Prediction).filter(Prediction.id == cls.p1.id).delete()
        cls.db.query(Hypothesis).filter(Hypothesis.id.in_([cls.h1_q1.id, cls.h2_q2.id])).delete()
        cls.db.query(DatasetVersion).filter(DatasetVersion.id == cls.dataset.id).delete()
        cls.db.query(ResearchQuestion).filter(ResearchQuestion.id.in_([cls.q1.id, cls.q2.id])).delete()
        cls.db.query(ResearchPlan).filter(ResearchPlan.project_id == cls.project.id).delete()
        cls.db.query(ResearchProject).filter(ResearchProject.id == cls.project.id).delete()
        cls.db.commit()
        cls.db.close()

    def test_investigation_planning_context_structure_and_relevance(self):
        """Verify Investigation Planning Context retrieves exact relevant records and excludes unrelated entities."""
        ctx = ScientificContextService.build_investigation_planning_context(
            db=self.db,
            dwh_db=None,
            question_id=self.q1.id,
            activate_orchestrator=False,
        )

        # 1. Project identity
        self.assertEqual(ctx.project.id, self.project.id)
        self.assertEqual(ctx.project.title, "Scientific Context Test Project")

        # 2. Approved ResearchPlan selected automatically
        self.assertIsNotNone(ctx.research_plan)
        self.assertEqual(ctx.research_plan.version, 2)
        self.assertEqual(ctx.research_plan.status, "approved")
        self.assertIn("morphological variation", ctx.research_plan.objective)

        # 3. Focal ResearchQuestion
        self.assertEqual(ctx.research_question.id, self.q1.id)
        self.assertIn("Atlantic and Indo-Pacific", ctx.research_question.text)

        # 4. Related Hypotheses included, Unrelated Hypotheses excluded
        h_ids = [h.id for h in ctx.hypotheses]
        self.assertIn(self.h1_q1.id, h_ids)
        self.assertNotIn(self.h2_q2.id, h_ids)  # Q2 hypothesis excluded!

        # 5. Prediction linked to Hypothesis included
        self.assertEqual(len(ctx.hypotheses[0].predictions), 1)
        self.assertEqual(ctx.hypotheses[0].predictions[0].id, self.p1.id)

        # 6. Datasets included
        ds_keys = [d.version_key for d in ctx.available_datasets]
        self.assertIn("TEST_DSV_01", ds_keys)

        # 7. Previous Results for Q1 included
        res_ids = [r.id for r in ctx.previous_results]
        self.assertIn(self.res_q1.id, res_ids)
        self.assertIn("PERMANOVA F=14.2", ctx.previous_results[0].summary)

        # 8. Relevant Decisions and Claims included
        dec_ids = [d.id for d in ctx.decisions]
        self.assertIn(self.decision.id, dec_ids)
        claim_ids = [c.id for c in ctx.claims]
        self.assertIn(self.claim.id, claim_ids)

        # 9. Constraints and Biases populated from approved plan
        self.assertIn("Depth gradient", ctx.known_constraints)
        self.assertIn("Museum sampling density", ctx.known_biases)

        # 10. Provenance records preserved
        prov_entity_types = [p.entity_type for p in ctx.provenance_records]
        self.assertIn("ResearchQuestion", prov_entity_types)
        self.assertIn("ResearchPlan", prov_entity_types)
        self.assertIn("Hypothesis", prov_entity_types)
        self.assertIn("Result", prov_entity_types)

    def test_investigation_planning_context_explicit_missing_information(self):
        """Verify explicit absence markers when information does not exist."""
        ctx_q2 = ScientificContextService.build_investigation_planning_context(
            db=self.db,
            dwh_db=None,
            question_id=self.q2.id,
            activate_orchestrator=False,
        )

        # Q2 has no predictions, no experiments, no results, no decisions
        self.assertEqual(len(ctx_q2.previous_results), 0)
        self.assertIn("No prior computational results produced for this question yet.", ctx_q2.missing_information)

    def test_prompt_renderer_formatting_and_no_secrets(self):
        """Verify prompt renderer produces clean sections without leaking credentials."""
        ctx = ScientificContextService.build_investigation_planning_context(
            db=self.db,
            dwh_db=None,
            question_id=self.q1.id,
            activate_orchestrator=False,
        )
        rendered = ScientificContextService.format_investigation_planning_context_for_prompt(ctx)

        self.assertIn("INVESTIGATION PLANNING CONTEXT", rendered)

        self.assertIn("--- 1. RESEARCH PROJECT", rendered)
        self.assertIn("--- 2. APPROVED RESEARCH PLAN", rendered)
        self.assertIn("--- 3. FOCAL RESEARCH QUESTION", rendered)
        self.assertIn("--- 4. RELATED HYPOTHESES & PREDICTIONS", rendered)
        self.assertIn("--- 5. AVAILABLE SCIENTIFIC DATASETS", rendered)
        self.assertIn("--- 6. PREVIOUS RESULTS & SCIENTIFIC EVIDENCE", rendered)
        self.assertIn("[PROVENANCE: DATABASE_WORLD_MODEL]", rendered)

        # Security check: No secret keywords
        self.assertNotIn("password", rendered.lower())
        self.assertNotIn("secret_key", rendered.lower())
        self.assertNotIn("api_key", rendered.lower())
        self.assertNotIn("bearer", rendered.lower())

    def test_capability_matching_context_builder(self):
        """Verify Capability Matching Context interface and pre-filtering."""
        cap_ctx = ScientificContextService.build_capability_matching_context(
            db=self.db,
            question_id=self.q1.id,
            step_goal="Extract foundation visual embeddings",
            category="vision_ml",
        )
        self.assertEqual(cap_ctx.metadata.context_type, ScientificContextType.CAPABILITY_MATCHING)
        self.assertEqual(cap_ctx.investigation_step_goal, "Extract foundation visual embeddings")
        self.assertGreaterEqual(len(cap_ctx.candidate_capabilities), 1)
        for c in cap_ctx.candidate_capabilities:
            self.assertTrue(c.is_enabled)

    def test_experiment_planning_context_builder(self):
        """Verify Experiment Planning Context interface."""
        exp_ctx = ScientificContextService.build_experiment_planning_context(
            db=self.db,
            question_id=self.q1.id,
            capability_key="studio_dinov3_embedding_extraction",
            hypothesis_id=self.h1_q1.id,
            dataset_version_id=self.dataset.id,
        )
        self.assertEqual(exp_ctx.metadata.context_type, ScientificContextType.EXPERIMENT_PLANNING)
        self.assertIsNotNone(exp_ctx.selected_capability)
        self.assertEqual(exp_ctx.selected_capability.capability_key, "studio_dinov3_embedding_extraction")
        self.assertEqual(exp_ctx.intended_dataset.version_key, "TEST_DSV_01")

    def test_result_interpretation_context_builder(self):
        """Verify Result Interpretation Context interface."""
        res_ctx = ScientificContextService.build_result_interpretation_context(
            db=self.db,
            analysis_run_id=self.run_q1.id,
        )
        self.assertEqual(res_ctx.metadata.context_type, ScientificContextType.RESULT_INTERPRETATION)
        self.assertEqual(res_ctx.run_status, "completed")
        self.assertEqual(len(res_ctx.results), 1)
        self.assertEqual(res_ctx.results[0].id, self.res_q1.id)

    def test_scientific_integrity_read_only_invariant(self):
        """Verify context construction is strictly read-only and creates no records."""
        initial_plans_cnt = self.db.query(AnalysisPlan).count()
        initial_runs_cnt = self.db.query(AnalysisRun).count()
        initial_results_cnt = self.db.query(Result).count()
        initial_hypotheses_cnt = self.db.query(Hypothesis).count()

        _ = ScientificContextService.build_investigation_planning_context(
            db=self.db,
            dwh_db=None,
            question_id=self.q1.id,
            activate_orchestrator=False,
        )

        self.assertEqual(self.db.query(AnalysisPlan).count(), initial_plans_cnt)
        self.assertEqual(self.db.query(AnalysisRun).count(), initial_runs_cnt)
        self.assertEqual(self.db.query(Result).count(), initial_results_cnt)
        self.assertEqual(self.db.query(Hypothesis).count(), initial_hypotheses_cnt)

    def test_brainstorming_context_backward_compatibility(self):
        """Verify existing build_brainstorming_context continues working unchanged."""
        bs_ctx = build_brainstorming_context(
            db=self.db,
            project_id=self.project.id,
            dwh_db=None,
            latest_user_message="Tell me about Nassarius",
        )
        self.assertIn("project_title", bs_ctx)
        self.assertIn("existing_questions", bs_ctx)
        self.assertIn("capabilities_context", bs_ctx)

    def test_api_endpoints_inspection(self):
        """Verify API inspect endpoints."""
        res = self.client.get(f"/context/investigation-planning/{self.q1.id}?orchestrator=false")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("context", data)
        self.assertIn("rendered_prompt", data)
        self.assertEqual(data["context"]["project"]["id"], self.project.id)


if __name__ == "__main__":
    unittest.main()
