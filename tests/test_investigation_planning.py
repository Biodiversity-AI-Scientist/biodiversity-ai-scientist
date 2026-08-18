import unittest
from fastapi.testclient import TestClient

from src.database import SessionLocal
from src.main import app
from src.models import (
    BrainstormingSession,
    InvestigationPlanGeneration,
    InvestigationStep,
    InvestigationStepDependency,
    ResearchPlan,
    ResearchProject,
    ResearchQuestion,
)
from src.repositories.investigation_step import (
    InvestigationStepRepository,
    check_for_cycle,
)
from src.schemas.investigation_step import (
    InvestigationStepCreate,
    InvestigationStepStatus,
    InvestigationStepUpdate,
)
from src.services.investigation_planning import InvestigationPlanningService


class TestInvestigationPlanning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.client = TestClient(app)

        cls.project = ResearchProject(
            title="Nassarius Cryptic Diversity Study",
            objective="Investigating morphological variation and cryptic diversity in Nassarius gastropods.",
        )

        cls.db.add(cls.project)
        cls.db.flush()

        cls.question = ResearchQuestion(
            project_id=cls.project.id,
            question="Do phenotypic shell clusters correspond to distinct genetic operational taxonomic units in Nassarius?",
        )
        cls.db.add(cls.question)
        cls.db.flush()

        cls.session = BrainstormingSession(
            project_id=cls.project.id,
            initial_idea="Study Nassarius shell morphology with computer vision",
            status="completed",
        )
        cls.db.add(cls.session)
        cls.db.flush()

        cls.plan = ResearchPlan(
            project_id=cls.project.id,
            brainstorming_session_id=cls.session.id,
            title="Approved Research Plan for Nassarius",
            content={
                "working_title": "Approved Research Plan for Nassarius",
                "research_objective": "Determine if conchological variation in Nassarius reflects cryptic speciation.",
                "primary_research_question": cls.question.question,
            },
            version=1,
            status="approved",
        )

        cls.db.add(cls.plan)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_01_cycle_detection_kahn_algorithm(self):
        # Linear DAG: A -> B -> C (no cycle)
        nodes = ["S1", "S2", "S3"]
        edges = [("S1", "S2"), ("S2", "S3")]
        self.assertFalse(check_for_cycle(nodes, edges))

        # Diamond DAG: S1 -> S2, S1 -> S3, S2 -> S4, S3 -> S4 (no cycle)
        nodes = ["S1", "S2", "S3", "S4"]
        edges = [("S1", "S2"), ("S1", "S3"), ("S2", "S4"), ("S3", "S4")]
        self.assertFalse(check_for_cycle(nodes, edges))

        # Simple 2-node cycle: S1 -> S2, S2 -> S1
        cycle_edges = [("S1", "S2"), ("S2", "S1")]
        self.assertTrue(check_for_cycle(["S1", "S2"], cycle_edges))

        # 3-node cycle: S1 -> S2 -> S3 -> S1
        cycle_edges_3 = [("S1", "S2"), ("S2", "S3"), ("S3", "S1")]
        self.assertTrue(check_for_cycle(["S1", "S2", "S3"], cycle_edges_3))

    def test_02_investigation_plan_generation_batch_entity(self):
        gen = InvestigationStepRepository.create_generation(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            research_plan_id=self.plan.id,
            summary_rationale="Comprehensive 5-step test workflow.",
            identified_uncertainties=["Data gap in museum vouchers"],
            model_provenance={"model": "test-model", "latency_ms": 120},
            context_summary={"project_id": self.project.id, "activated_layers": ["data", "domain"]},
        )
        self.db.commit()

        self.assertIsNotNone(gen.id)
        self.assertEqual(gen.summary_rationale, "Comprehensive 5-step test workflow.")
        self.assertEqual(gen.identified_uncertainties, ["Data gap in museum vouchers"])
        self.assertEqual(gen.model_provenance["model"], "test-model")

        # Verify listing
        generations = InvestigationStepRepository.list_generations_for_question(self.db, self.question.id)
        self.assertGreaterEqual(len(generations), 1)
        self.assertEqual(generations[0].id, gen.id)

    def test_03_computed_is_blocked_strict_semantics(self):
        # Create Step 1 (Prerequisite)
        step1 = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            data=InvestigationStepCreate(
                title="Step 1: Taxonomic verification",
                scientific_goal="Verify taxa",
                rationale="Needed first",
                step_type="taxonomy",
                status=InvestigationStepStatus.PROPOSED,
                display_order=1,
            ),
            research_plan_id=self.plan.id,
        )

        # Create Step 2 (Depends on Step 1)
        step2 = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            data=InvestigationStepCreate(
                title="Step 2: Representation extraction",
                scientific_goal="Extract features",
                rationale="Requires validated taxonomy",
                step_type="representation",
                status=InvestigationStepStatus.PROPOSED,
                display_order=2,
                prerequisite_step_ids=[step1.id],
            ),
            research_plan_id=self.plan.id,
        )
        self.db.commit()

        # Initially, Step 1 is 'proposed' -> Step 2 must be is_blocked=True
        resps = InvestigationStepRepository.list_step_responses_for_question(self.db, self.question.id)
        r_map = {r.id: r for r in resps}
        self.assertFalse(r_map[step1.id].is_blocked)
        self.assertTrue(r_map[step2.id].is_blocked)

        # Step 1 becomes 'in_progress' -> Step 2 is still blocked
        InvestigationStepRepository.update_step(
            self.db, step1.id, InvestigationStepUpdate(status=InvestigationStepStatus.IN_PROGRESS)
        )
        self.db.commit()
        resps = InvestigationStepRepository.list_step_responses_for_question(self.db, self.question.id)
        r_map = {r.id: r for r in resps}
        self.assertTrue(r_map[step2.id].is_blocked)

        # Step 1 becomes 'skipped' -> STRICT RULE: Step 2 MUST REMAIN BLOCKED!
        InvestigationStepRepository.update_step(
            self.db, step1.id, InvestigationStepUpdate(status=InvestigationStepStatus.SKIPPED)
        )
        self.db.commit()
        resps = InvestigationStepRepository.list_step_responses_for_question(self.db, self.question.id)
        r_map = {r.id: r for r in resps}
        self.assertTrue(
            r_map[step2.id].is_blocked,
            "Skipped prerequisite must NOT automatically satisfy dependency!",
        )

        # Step 1 becomes 'completed' -> Step 2 becomes is_blocked=False
        InvestigationStepRepository.update_step(
            self.db, step1.id, InvestigationStepUpdate(status=InvestigationStepStatus.COMPLETED)
        )
        self.db.commit()
        resps = InvestigationStepRepository.list_step_responses_for_question(self.db, self.question.id)
        r_map = {r.id: r for r in resps}
        self.assertFalse(
            r_map[step2.id].is_blocked,
            "Completed prerequisite satisfies dependency.",
        )

    def test_04_add_circular_dependency_rejected(self):
        s1 = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            data=InvestigationStepCreate(
                title="S1", scientific_goal="G1", rationale="R1", step_type="data_assessment", display_order=1
            ),
        )
        s2 = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            data=InvestigationStepCreate(
                title="S2", scientific_goal="G2", rationale="R2", step_type="representation", display_order=2,
                prerequisite_step_ids=[s1.id]
            ),
        )
        self.db.commit()

        # Trying to make S1 depend on S2 (introducing S1 -> S2 -> S1 cycle) must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            InvestigationStepRepository.add_dependency(self.db, step_id=s1.id, depends_on_step_id=s2.id)
        self.assertIn("circular dependency cycle", str(ctx.exception))

        # Self-dependency must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            InvestigationStepRepository.add_dependency(self.db, step_id=s1.id, depends_on_step_id=s1.id)
        self.assertIn("cannot depend on itself", str(ctx.exception))

    def test_05_archive_vs_hard_delete(self):
        # Proposed step -> hard delete
        s_prop = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            data=InvestigationStepCreate(
                title="Draft Step", scientific_goal="G", rationale="R", step_type="data_assessment",
                status=InvestigationStepStatus.PROPOSED
            ),
        )
        self.db.commit()
        prop_id = s_prop.id

        self.assertTrue(InvestigationStepRepository.delete_or_archive_step(self.db, prop_id))
        self.db.commit()
        self.assertIsNone(self.db.get(InvestigationStep, prop_id))

        # Approved step -> soft archive
        s_app = InvestigationStepRepository.create_step(
            db=self.db,
            project_id=self.project.id,
            question_id=self.question.id,
            data=InvestigationStepCreate(
                title="Approved Historical Step", scientific_goal="G", rationale="R", step_type="data_assessment",
                status=InvestigationStepStatus.APPROVED
            ),
        )
        self.db.commit()
        app_id = s_app.id

        self.assertTrue(InvestigationStepRepository.delete_or_archive_step(self.db, app_id))
        self.db.commit()
        archived_step = self.db.get(InvestigationStep, app_id)
        self.assertIsNotNone(archived_step)
        self.assertIsNotNone(archived_step.archived_at)

    def test_06_investigation_planning_service_generate_plan(self):
        res = InvestigationPlanningService.generate_plan_for_question(
            db=self.db,
            dwh_db=None,
            question_id=self.question.id,
            research_plan_id=self.plan.id,
            user_guidance="Focus on geometric morphometrics and WoRMS standardization",
            focus_areas=["taxonomy", "morphometrics"],
        )

        self.assertIsNotNone(res.id)
        self.assertEqual(res.project_id, self.project.id)
        self.assertEqual(res.question_id, self.question.id)
        self.assertEqual(res.research_plan_id, self.plan.id)
        self.assertGreaterEqual(len(res.steps), 3)
        self.assertIsNotNone(res.summary_rationale)

        # Verify DAG properties in generated response
        steps = res.steps
        step_ids = [s.id for s in steps]
        for s in steps:
            for pid in s.prerequisite_step_ids:
                self.assertIn(pid, step_ids)
                self.assertNotEqual(pid, s.id)

        # Verify DAG endpoint
        dag = InvestigationStepRepository.get_dag_for_question(self.db, self.question.id)
        self.assertGreaterEqual(dag.total_steps, len(steps))
        self.assertGreaterEqual(len(dag.nodes), len(steps))


    def test_07_fastapi_endpoints_investigation_planning(self):
        # 1. Generate plan via API
        resp = self.client.post(
            f"/questions/{self.question.id}/investigation-plan/generate",
            json={"research_plan_id": self.plan.id, "user_guidance": "Test guidance"},
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["question_id"], self.question.id)
        self.assertGreaterEqual(len(data["steps"]), 3)
        first_step_id = data["steps"][0]["id"]
        second_step_id = data["steps"][1]["id"]

        # 2. List generations
        resp = self.client.get(f"/questions/{self.question.id}/investigation-plan/generations")
        self.assertEqual(resp.status_code, 200)
        gens = resp.json()
        self.assertGreaterEqual(len(gens), 1)

        # 3. List steps
        resp = self.client.get(f"/questions/{self.question.id}/investigation-steps")
        self.assertEqual(resp.status_code, 200)
        steps = resp.json()
        self.assertGreaterEqual(len(steps), 3)

        # 4. Get DAG
        resp = self.client.get(f"/questions/{self.question.id}/investigation-steps/dag")
        self.assertEqual(resp.status_code, 200)
        dag = resp.json()
        self.assertGreaterEqual(dag["total_steps"], 3)

        # 5. Patch step status to approved
        resp = self.client.patch(f"/investigation-steps/{first_step_id}", json={"status": "approved"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "approved")

        # 6. Add dependency
        resp = self.client.post(f"/investigation-steps/{second_step_id}/dependencies?depends_on_step_id={first_step_id}")
        self.assertIn(resp.status_code, (201, 200))

        # 7. Remove dependency
        resp = self.client.delete(f"/investigation-steps/{second_step_id}/dependencies/{first_step_id}")
        self.assertEqual(resp.status_code, 204)

        # 8. Create manual step
        resp = self.client.post(
            f"/questions/{self.question.id}/investigation-steps",
            json={
                "title": "Manual Verification Step",
                "scientific_goal": "Check vouchers",
                "rationale": "Museum audit",
                "step_type": "data_assessment",
                "requires_capability": True,
                "requires_experiment": False,
            },
        )
        self.assertEqual(resp.status_code, 201)
        manual_id = resp.json()["id"]

        # 9. Delete step
        resp = self.client.delete(f"/investigation-steps/{manual_id}")
        self.assertEqual(resp.status_code, 204)


if __name__ == "__main__":
    unittest.main()
