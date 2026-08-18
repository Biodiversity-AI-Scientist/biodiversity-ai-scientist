import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app
from src.models import AnalysisPlan, ResearchProject, ResearchQuestion
from src.schemas.analysis_run import AnalysisRunCreate
from src.services import analysis_run as service


class AnalysisRunLifecycleTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(
            bind=cls.engine,
            expire_on_commit=False,
        )

        def override_get_db():
            db = cls.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self) -> None:
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.Session()

    def tearDown(self) -> None:
        self.db.close()

    def create_plan(self) -> AnalysisPlan:
        project = ResearchProject(title="Lifecycle test project")
        self.db.add(project)
        self.db.flush()
        question = ResearchQuestion(
            project_id=project.id,
            question="Does the lifecycle preserve provenance?",
        )
        self.db.add(question)
        self.db.flush()
        plan = AnalysisPlan(
            question_id=question.id,
            method="Lifecycle framework test",
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def test_create_run_for_existing_plan(self) -> None:
        plan = self.create_plan()

        response = self.client.post(
            f"/analysis-plans/{plan.id}/runs",
            json={},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["analysis_plan_id"], plan.id)
        self.assertEqual(payload["status"], "pending")
        self.assertIsNone(payload["started_at"])
        self.assertIsNone(payload["completed_at"])

    def test_create_run_for_nonexistent_plan_returns_404(self) -> None:
        response = self.client.post(
            "/analysis-plans/999/runs",
            json={},
        )
        self.assertEqual(response.status_code, 404)

    def test_read_and_list_runs_for_plan(self) -> None:
        plan = self.create_plan()
        created = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )

        read_response = self.client.get(
            f"/analysis-runs/{created.id}"
        )
        list_response = self.client.get(
            f"/analysis-plans/{plan.id}/runs"
        )

        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.json()["id"], created.id)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in list_response.json()],
            [created.id],
        )

    def test_pending_running_completed_lifecycle(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )

        run = service.start_analysis_run(self.db, run.id)
        self.assertEqual(run.status, "running")
        self.assertIsNotNone(run.started_at)

        run = service.complete_analysis_run(self.db, run.id)
        self.assertEqual(run.status, "completed")
        self.assertIsNotNone(run.completed_at)
        self.assertIsNone(run.error_message)

    def test_pending_running_failed_lifecycle(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )

        service.start_analysis_run(self.db, run.id)
        run = service.fail_analysis_run(
            self.db,
            run.id,
            "Validated executor raised an error",
        )

        self.assertEqual(run.status, "failed")
        self.assertIsNotNone(run.completed_at)
        self.assertEqual(
            run.error_message,
            "Validated executor raised an error",
        )
        self.assertNotEqual(run.status, "completed")

    def test_invalid_transition_is_rejected(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )

        with self.assertRaises(
            service.InvalidAnalysisRunTransitionError
        ):
            service.complete_analysis_run(self.db, run.id)

        self.db.refresh(run)
        self.assertEqual(run.status, "pending")
        self.assertIsNone(run.completed_at)

    def test_public_patch_cannot_change_lifecycle_status(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )

        response = self.client.patch(
            f"/analysis-runs/{run.id}",
            json={"status": "completed"},
        )

        self.assertEqual(response.status_code, 422)

        self.db.refresh(run)
        self.assertEqual(run.status, "pending")
        self.assertIsNone(run.completed_at)

    def test_running_run_metadata_is_immutable(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )
        service.start_analysis_run(self.db, run.id)

        response = self.client.patch(
            f"/analysis-runs/{run.id}",
            json={"model_version": "changed-after-start"},
        )

        self.assertEqual(response.status_code, 409)
        self.db.refresh(run)
        self.assertIsNone(run.model_version)

    def test_running_run_can_be_explicitly_marked_failed(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )
        service.start_analysis_run(self.db, run.id)

        response = self.client.post(
            f"/analysis-runs/{run.id}/fail",
            json={
                "reason": (
                    "Execution process ended before producing a result"
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "failed")
        self.assertIsNotNone(payload["completed_at"])
        self.assertEqual(
            payload["error_message"],
            "Execution process ended before producing a result",
        )

    def test_pending_run_cannot_be_marked_failed(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(),
        )

        response = self.client.post(
            f"/analysis-runs/{run.id}/fail",
            json={"reason": "No execution was started"},
        )

        self.assertEqual(response.status_code, 409)
        self.db.refresh(run)
        self.assertEqual(run.status, "pending")

    def test_parameter_overrides_stored_in_run(self) -> None:
        plan = self.create_plan()
        plan.parameters = {"batch_size": 32, "epochs": 50}
        self.db.commit()

        # Run overrides batch_size to 24 due to GPU memory constraints
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(parameters={"batch_size": 24, "epochs": 50}),
        )

        self.assertEqual(run.parameters["batch_size"], 24)
        self.assertEqual(plan.parameters["batch_size"], 32)  # Plan preserved proposed parameters

    def test_execution_metadata_and_structured_error_diagnostics(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(
                execution_metadata={"environment": "cuda:0", "driver": "535.183"},
                tool_name="torch_trainer",
                tool_version="2.2.0",
            ),
        )
        self.assertEqual(run.execution_metadata["environment"], "cuda:0")

        # Start run with updated runtime metadata
        start_res = self.client.post(
            f"/analysis-runs/{run.id}/start",
            json={"execution_metadata": {"host": "node-gpu-4"}},
        )
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.json()["status"], "running")
        self.assertEqual(start_res.json()["execution_metadata"]["host"], "node-gpu-4")

        # Fail run with structured error details
        fail_res = self.client.post(
            f"/analysis-runs/{run.id}/fail",
            json={
                "error_message": "CUDA out of memory while allocating 4.2 GiB",
                "error_type": "OutOfMemoryError",
                "error_details": {"allocated_mb": 11800, "requested_mb": 4200, "gpu_id": 0},
            },
        )
        self.assertEqual(fail_res.status_code, 200)
        payload = fail_res.json()
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error_type"], "OutOfMemoryError")
        self.assertIn("CUDA out of memory", payload["error_message"])
        self.assertEqual(payload["error_details"]["gpu_id"], 0)

    def test_complete_endpoint_lifecycle(self) -> None:
        plan = self.create_plan()
        run = service.create_analysis_run(self.db, plan.id, AnalysisRunCreate())
        service.start_analysis_run(self.db, run.id)

        complete_res = self.client.post(
            f"/analysis-runs/{run.id}/complete",
            json={"execution_metadata": {"exit_code": 0, "duration_s": 42.5}},
        )
        self.assertEqual(complete_res.status_code, 200)
        self.assertEqual(complete_res.json()["status"], "completed")
        self.assertIsNotNone(complete_res.json()["completed_at"])
        self.assertEqual(complete_res.json()["execution_metadata"]["exit_code"], 0)

    def test_project_run_listing_returns_404_for_missing_project(
        self,
    ) -> None:
        response = self.client.get(
            "/projects/999/analysis-runs"
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()

