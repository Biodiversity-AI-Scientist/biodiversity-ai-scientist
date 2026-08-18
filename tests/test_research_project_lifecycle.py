import unittest
from fastapi.testclient import TestClient

from src.database import SessionLocal
from src.main import app
from src.models import (
    BrainstormingSession,
    InvestigationPlanGeneration,
    InvestigationStep,
    ResearchPlan,
    ResearchProject,
    ResearchQuestion,
)
from src.repositories.investigation_step import InvestigationStepRepository
from src.schemas.investigation_step import InvestigationStepCreate, InvestigationStepStatus
from src.schemas.research_project import ResearchProjectCreate


class TestResearchProjectLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_project_archive_unarchive_lifecycle(self):
        # 1. Create project
        resp = self.client.post(
            "/projects",
            json={"title": "Temporary Test Project for Archive", "objective": "Testing lifecycle"},
        )
        self.assertEqual(resp.status_code, 201)
        project_id = resp.json()["id"]

        # 2. Verify in active listing
        resp = self.client.get("/projects")
        self.assertEqual(resp.status_code, 200)
        active_ids = [p["id"] for p in resp.json()]
        self.assertIn(project_id, active_ids)

        # 3. Archive project
        resp = self.client.post(f"/projects/{project_id}/archive")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "archived")
        self.assertIsNotNone(resp.json()["archived_at"])

        # 4. Verify hidden from active listing
        resp = self.client.get("/projects")
        self.assertEqual(resp.status_code, 200)
        active_ids = [p["id"] for p in resp.json()]
        self.assertNotIn(project_id, active_ids)

        # 5. Verify visible in include_archived=true listing
        resp = self.client.get("/projects?include_archived=true")
        self.assertEqual(resp.status_code, 200)
        all_ids = [p["id"] for p in resp.json()]
        self.assertIn(project_id, all_ids)

        # 6. Unarchive project
        resp = self.client.post(f"/projects/{project_id}/unarchive")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "active")
        self.assertIsNone(resp.json()["archived_at"])

        # 7. Verify back in active listing
        resp = self.client.get("/projects")
        self.assertEqual(resp.status_code, 200)
        active_ids = [p["id"] for p in resp.json()]
        self.assertIn(project_id, active_ids)

        # 8. Attempt to delete active project directly -> MUST FAIL with HTTP 400
        del_resp = self.client.delete(f"/projects/{project_id}")
        self.assertEqual(del_resp.status_code, 400)
        self.assertIn("Cannot delete an active", del_resp.json()["detail"])

        # 9. Archive project and then delete -> MUST SUCCEED with HTTP 204
        self.client.post(f"/projects/{project_id}/archive")
        del_resp = self.client.delete(f"/projects/{project_id}")
        self.assertEqual(del_resp.status_code, 204)

    def test_project_cascade_delete_all_child_info(self):
        # 1. Create project with multiple child entities
        project = ResearchProject(
            title="Cascade Delete Test Project",
            objective="Verifying cascade delete across all child tables",
        )
        self.db.add(project)
        self.db.flush()
        pid = project.id

        question = ResearchQuestion(
            project_id=pid,
            question="Cascade question?",
        )
        self.db.add(question)
        self.db.flush()
        qid = question.id

        session = BrainstormingSession(
            project_id=pid,
            initial_idea="Brainstorm idea",
            status="completed",
        )
        self.db.add(session)
        self.db.flush()

        plan = ResearchPlan(
            project_id=pid,
            brainstorming_session_id=session.id,
            title="Cascade Plan",
            content={"working_title": "Cascade Plan"},
            version=1,
            status="approved",
        )
        self.db.add(plan)
        self.db.flush()

        gen = InvestigationStepRepository.create_generation(
            db=self.db,
            project_id=pid,
            question_id=qid,
            research_plan_id=plan.id,
            summary_rationale="Generation summary",
            identified_uncertainties=[],
            model_provenance={},
            context_summary={},
        )
        self.db.flush()

        step1 = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=pid,
            question_id=qid,
            data=InvestigationStepCreate(
                title="Child Step 1",
                scientific_goal="Goal 1",
                rationale="Rationale 1",
                step_type="taxonomy",
            ),
            generation_id=gen.id,
            research_plan_id=plan.id,
        )
        step2 = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=pid,
            question_id=qid,
            data=InvestigationStepCreate(
                title="Child Step 2",
                scientific_goal="Goal 2",
                rationale="Rationale 2",
                step_type="representation",
                prerequisite_step_ids=[step1.id],
            ),
            generation_id=gen.id,
            research_plan_id=plan.id,
        )
        self.db.commit()

        plan_id = plan.id
        session_id = session.id
        gen_id = gen.id
        step1_id = step1.id
        step2_id = step2.id

        # Verify children exist
        self.assertIsNotNone(self.db.get(ResearchProject, pid))
        self.assertIsNotNone(self.db.get(ResearchQuestion, qid))
        self.assertIsNotNone(self.db.get(InvestigationStep, step1_id))
        self.assertIsNotNone(self.db.get(InvestigationStep, step2_id))

        # 2. Execute cascade delete via API
        resp = self.client.delete(f"/projects/{pid}")
        self.assertEqual(resp.status_code, 204)

        # 3. Verify project and all child info are completely deleted
        self.db.expire_all()
        self.assertIsNone(self.db.get(ResearchProject, pid))
        self.assertIsNone(self.db.get(ResearchQuestion, qid))
        self.assertIsNone(self.db.get(ResearchPlan, plan_id))
        self.assertIsNone(self.db.get(BrainstormingSession, session_id))
        self.assertIsNone(self.db.get(InvestigationPlanGeneration, gen_id))
        self.assertIsNone(self.db.get(InvestigationStep, step1_id))
        self.assertIsNone(self.db.get(InvestigationStep, step2_id))



if __name__ == "__main__":
    unittest.main()
