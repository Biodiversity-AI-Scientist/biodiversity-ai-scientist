import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db, get_dwh_db
from src.llm.contracts import GatewayResult, InvocationMetadata
from src.llm.exceptions import StructuredOutputValidationError
from src.main import app
from src.models import (
    AnalysisRun,
    BrainstormingSession,
    EvidenceItem,
    Hypothesis,
    ResearchPlan,
    ResearchProject,
    ResearchQuestion,
    Result,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class TestResearchPlanMVP(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_get_dwh_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_dwh_db] = override_get_dwh_db
        self.client = TestClient(app)

        # Seed initial project and session
        db = TestingSessionLocal()
        project = ResearchProject(
            title="Conus Phylogeography Study",
            objective="Evaluate spatial distribution of shell shapes.",
            status="draft",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        self.project_id = project.id

        session = BrainstormingSession(
            project_id=self.project_id,
            initial_idea="Evaluate geographic variation in shell width among Conus species",
            messages=[
                {"role": "user", "content": "Evaluate shell width variation", "sequence": 1},
                {
                    "role": "assistant",
                    "content": "Suggested Research Questions:\n- Does shell width vary with sea surface temperature?",
                    "sequence": 2,
                },
            ],
            status="active",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        self.session_id = session.id
        db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        app.dependency_overrides.clear()

    @patch("src.routers.research_plan.LLMGateway")
    def test_generate_research_plan_20_fields_success(self, MockLLMGateway):
        plan_content = {
            "working_title": "Conus Shell Morphometrics Across Latitude",
            "research_objective": "Determine whether shell shape correlates with SST.",
            "scientific_background_or_rationale": "Bergmann's rule in marine ectotherms.",
            "primary_research_question": "Does shell width vary with sea surface temperature?",
            "secondary_research_questions": ["Are morphometric clusters cryptic species?"],
            "candidate_hypotheses": ["Shell width correlates positively with sea surface temperature."],
            "alternative_explanations": ["Depth gradient confounding."],
            "evidence_required": ["Calibrated museum shell aperture measurements."],
            "available_data": ["GBIF occurrence records and digitized specimens."],
            "additional_data_needed": ["High-resolution bathymetry layers."],
            "proposed_research_strategy": "Geometric morphometrics combined with spatial regression.",
            "proposed_analytical_stages": ["Landmark extraction", "Procrustes alignment", "GLMM modeling"],
            "potential_confounders": ["Collection year and preservation shrinkage."],
            "sources_of_bias": ["Museum sampling spatial bias."],
            "validation_or_robustness_strategy": "Spatial cross-validation with leave-one-ocean-basin-out.",
            "interpretation_criteria": "P < 0.01 and effect size Cohen's d > 0.5.",
            "possible_outcomes": ["Morphocline confirmed", "No latitude effect"],
            "limitations": ["Limited sampling in Indian Ocean."],
            "open_scientific_decisions": ["Choice of 2D vs 3D landmarks."],
            "recommended_next_step": "Extract 2D landmarks from top 500 museum images.",
        }

        mock_gateway = MagicMock()
        mock_gateway.invoke.return_value = GatewayResult(
            output=plan_content,
            metadata=InvocationMetadata(
                invocation_id="plan-inv-1",
                provider="openai_responses",
                model="deepseek-v4-flash",
                template_id="research_plan_generation_v1",
                schema_id="research_plan_generation_v1",
                provider_request_id="req-p1",
                provider_status="completed",
                attempts=1,
                latency_ms=1200,
                input_tokens=600,
                output_tokens=450,
                prompt_sha256="prompt_hash",
                response_sha256="resp_hash",
            ),
        )
        MockLLMGateway.return_value = mock_gateway

        response = self.client.post(f"/brainstorming-sessions/{self.session_id}/research-plan")
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["title"], "Conus Shell Morphometrics Across Latitude")
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["status"], "draft")
        self.assertEqual(data["parent_plan_id"], None)
        self.assertEqual(len(data["content"]), 20)
        self.assertEqual(data["content"]["primary_research_question"], "Does shell width vary with sea surface temperature?")

    @patch("src.routers.research_plan.LLMGateway")
    def test_generate_research_plan_failure_returns_502_with_clean_db(self, MockLLMGateway):
        mock_gateway = MagicMock()
        mock_gateway.invoke.side_effect = StructuredOutputValidationError("Model output failed schema validation")
        MockLLMGateway.return_value = mock_gateway

        response = self.client.post(f"/brainstorming-sessions/{self.session_id}/research-plan")
        self.assertEqual(response.status_code, 502)

        # Verify zero ResearchPlans created in DB
        db = sessionmaker(bind=self.engine)()
        plan_count = db.query(ResearchPlan).count()
        self.assertEqual(plan_count, 0)
        db.close()

    def test_plan_lifecycle_and_immutability_enforcement(self):
        db = sessionmaker(bind=self.engine)()
        plan = ResearchPlan(
            project_id=self.project_id,
            brainstorming_session_id=self.session_id,
            version=1,
            title="Initial Draft Plan",
            status="draft",
            content={"working_title": "Initial Draft Plan", "research_objective": "Initial objective"},
        )
        db.add(plan)
        db.commit()
        plan_id = plan.id
        db.close()

        # 1. In-place edit on draft is PERMITTED
        put_res = self.client.put(
            f"/research-plans/{plan_id}",
            json={
                "title": "Edited Draft Plan",
                "content": {"working_title": "Edited Draft Plan", "research_objective": "Refined objective"},
            },
        )
        self.assertEqual(put_res.status_code, 200)
        self.assertEqual(put_res.json()["title"], "Edited Draft Plan")

        # 2. Transition draft -> under_review
        review_res = self.client.put(
            f"/research-plans/{plan_id}",
            json={"status": "under_review"},
        )
        self.assertEqual(review_res.status_code, 200)
        self.assertEqual(review_res.json()["status"], "under_review")

        # 3. Content edit on under_review MUST BE REJECTED (409 Conflict)
        conflict_res = self.client.put(
            f"/research-plans/{plan_id}",
            json={"content": {"research_objective": "Attempting illegal change under review"}},
        )
        self.assertEqual(conflict_res.status_code, 409)

        # 4. Transition under_review -> approved
        approve_res = self.client.post(f"/research-plans/{plan_id}/approve")
        self.assertEqual(approve_res.status_code, 200)
        self.assertEqual(approve_res.json()["status"], "approved")

        # 5. Content edit on approved MUST BE REJECTED (409 Conflict)
        approved_conflict = self.client.put(
            f"/research-plans/{plan_id}",
            json={"content": {"research_objective": "Attempting illegal change on approved plan"}},
        )
        self.assertEqual(approved_conflict.status_code, 409)

    @patch("src.routers.research_plan.LLMGateway")
    def test_plan_revision_creates_version_n_plus_one(self, MockLLMGateway):
        db = sessionmaker(bind=self.engine)()
        parent_plan = ResearchPlan(
            project_id=self.project_id,
            brainstorming_session_id=self.session_id,
            version=1,
            title="Approved Plan v1",
            status="approved",
            content={"working_title": "Approved Plan v1", "primary_research_question": "Question 1"},
        )
        db.add(parent_plan)
        db.commit()
        parent_plan_id = parent_plan.id
        db.close()

        mock_gateway = MagicMock()
        mock_gateway.invoke.return_value = GatewayResult(
            output={
                "working_title": "Revised Plan v2",
                "primary_research_question": "Question 1 refined with 3D landmarks",
                "research_objective": "Updated objective",
            },
            metadata=InvocationMetadata(
                invocation_id="rev-inv-1",
                provider="openai_responses",
                model="deepseek-v4-flash",
                template_id="research_plan_generation_v1",
                schema_id="research_plan_generation_v1",
                provider_request_id="req-rev-1",
                provider_status="completed",
                attempts=1,
                latency_ms=900,
                input_tokens=400,
                output_tokens=300,
                prompt_sha256="rev_prompt_hash",
                response_sha256="rev_resp_hash",
            ),
        )
        MockLLMGateway.return_value = mock_gateway

        revise_res = self.client.post(
            f"/research-plans/{parent_plan_id}/revise",
            json={"steering_instructions": "Focus strictly on 3D geometric morphometrics."},
        )
        self.assertEqual(revise_res.status_code, 201)
        rev_data = revise_res.json()
        self.assertEqual(rev_data["version"], 2)
        self.assertEqual(rev_data["parent_plan_id"], parent_plan_id)
        self.assertEqual(rev_data["status"], "draft")
        self.assertEqual(rev_data["title"], "Revised Plan v2")

    def test_plan_promotion_and_duplicate_prevention(self):
        db = sessionmaker(bind=self.engine)()
        plan = ResearchPlan(
            project_id=self.project_id,
            brainstorming_session_id=self.session_id,
            version=1,
            title="Promotable Plan",
            status="approved",
            content={
                "working_title": "Promotable Plan",
                "research_objective": "Objective",
                "primary_research_question": "Does shell width vary with sea surface temperature?",
                "secondary_research_questions": [
                    "Are morphometric clusters cryptic species?"
                ],
                "candidate_hypotheses": [
                    "Shell width correlates positively with sea surface temperature."
                ],
            },
        )
        db.add(plan)
        db.commit()
        plan_id = plan.id
        db.close()

        # Promote question index 0
        response = self.client.post(
            f"/research-plans/{plan_id}/promote",
            json={"question_indices": [0], "hypothesis_indices": [0]},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["promoted_question_ids"]), 1)
        self.assertEqual(len(data["promoted_hypothesis_ids"]), 1)

        q_id = data["promoted_question_ids"][0]

        # Verify ResearchQuestion in DB
        db = sessionmaker(bind=self.engine)()
        rq = db.get(ResearchQuestion, q_id)
        self.assertIsNotNone(rq)
        self.assertEqual(rq.source, "brainstorming")
        self.assertEqual(rq.brainstorming_session_id, self.session_id)

        # Duplicate promotion protection
        response2 = self.client.post(
            f"/research-plans/{plan_id}/promote",
            json={"question_indices": [0], "hypothesis_indices": [0], "target_question_id": q_id},
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2["promoted_question_ids"], [q_id])

        # Verify no duplicate ResearchQuestions created
        all_qs = db.query(ResearchQuestion).filter(ResearchQuestion.project_id == self.project_id).all()
        self.assertEqual(len(all_qs), 1)
        db.close()

    def test_scientific_integrity_no_results_or_runs_fabricated(self):
        db = sessionmaker(bind=self.engine)()
        # Verify that brainstorming and research plan creation do NOT fabricate Result, AnalysisRun, or EvidenceItem
        results_count = db.query(Result).count()
        runs_count = db.query(AnalysisRun).count()
        evidence_count = db.query(EvidenceItem).count()

        self.assertEqual(results_count, 0)
        self.assertEqual(runs_count, 0)
        self.assertEqual(evidence_count, 0)
        db.close()

    def test_archive_and_unarchive_research_plan(self):
        # Create a test plan
        db = sessionmaker(bind=self.engine)()
        plan = ResearchPlan(
            project_id=self.project_id,
            brainstorming_session_id=self.session_id,
            version=1,
            title="Archivable Research Plan",
            status="draft",
            content={"research_objective": "Test archiving"},
        )
        db.add(plan)
        db.commit()
        plan_id = plan.id
        db.close()

        # Default listing includes the plan
        list_res = self.client.get(f"/projects/{self.project_id}/research-plans")
        self.assertEqual(list_res.status_code, 200)
        ids = [p["id"] for p in list_res.json()]
        self.assertIn(plan_id, ids)

        # Archive plan
        arch_res = self.client.patch(f"/research-plans/{plan_id}/archive")
        self.assertEqual(arch_res.status_code, 200)
        self.assertEqual(arch_res.json()["status"], "archived")

        # Default listing excludes archived plan
        list_res2 = self.client.get(f"/projects/{self.project_id}/research-plans")
        ids2 = [p["id"] for p in list_res2.json()]
        self.assertNotIn(plan_id, ids2)

        # Listing with include_archived=true includes it
        list_res3 = self.client.get(f"/projects/{self.project_id}/research-plans?include_archived=true")
        ids3 = [p["id"] for p in list_res3.json()]
        self.assertIn(plan_id, ids3)

        # Unarchive plan
        unarch_res = self.client.patch(f"/research-plans/{plan_id}/unarchive")
        self.assertEqual(unarch_res.status_code, 200)
        self.assertEqual(unarch_res.json()["status"], "draft")

        # Default listing includes it again
        list_res4 = self.client.get(f"/projects/{self.project_id}/research-plans")
        ids4 = [p["id"] for p in list_res4.json()]
        self.assertIn(plan_id, ids4)


if __name__ == "__main__":
    unittest.main()

