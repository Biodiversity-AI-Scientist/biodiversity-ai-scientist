import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.executors.base import AnalysisComputationError
from src.executors.dataset_registration_summary import (
    DatasetRegistrationSummaryExecutor,
    DatasetRegistrationSummaryParameters,
)
from src.executors.registry import (
    EXECUTORS,
    UnknownAnalysisTypeError,
    get_executor,
)
from src.main import app
from src.models import (
    AnalysisPlan,
    AnalysisRun,
    DatasetVersion,
    ResearchProject,
    ResearchQuestion,
    Result,
)
from src.schemas.analysis_run import AnalysisRunCreate
from src.services import analysis_run


class FailingParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FailingExecutor:
    analysis_type = "failing_test_executor"
    version = "test"
    parameter_schema = FailingParameters

    def execute(self, context):
        raise AnalysisComputationError(
            "deterministic executor failure"
        )


class AnalysisExecutionTestCase(unittest.TestCase):
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

    def create_run(
        self,
        method: str = "dataset_registration_summary",
        parameters: dict | None = None,
        plan_has_dataset: bool = True,
    ) -> tuple[AnalysisRun, DatasetVersion]:
        project = ResearchProject(title="Executor test project")
        self.db.add(project)
        self.db.flush()
        question = ResearchQuestion(
            project_id=project.id,
            question="What is registered for this dataset?",
        )
        self.db.add(question)
        self.db.flush()
        dataset = DatasetVersion(
            project_id=project.id,
            version_key=f"DSV-TEST-{method}",
            source_system="deterministic-test",
            selection_definition={"accepted": True},
            member_count=7,
            grouping_keys=["specimen_id", "source_group"],
        )
        self.db.add(dataset)
        self.db.flush()
        plan = AnalysisPlan(
            question_id=question.id,
            dataset_version_id=(
                dataset.id if plan_has_dataset else None
            ),
            method=method,
            parameters=parameters,
        )
        self.db.add(plan)
        self.db.commit()
        run = analysis_run.create_analysis_run(
            self.db,
            plan.id,
            AnalysisRunCreate(
                dataset_version_id=(
                    None if plan_has_dataset else dataset.id
                )
            ),
        )
        return run, dataset

    def test_known_and_unknown_executor_resolution(self) -> None:
        executor = get_executor("dataset_registration_summary")
        self.assertIsInstance(
            executor,
            DatasetRegistrationSummaryExecutor,
        )
        with self.assertRaises(UnknownAnalysisTypeError):
            get_executor("not_registered")

    def test_parameter_schema_accepts_empty_and_rejects_unknown(self) -> None:
        validated = (
            DatasetRegistrationSummaryParameters.model_validate({})
        )
        self.assertEqual(validated.model_dump(), {})
        with self.assertRaises(Exception):
            DatasetRegistrationSummaryParameters.model_validate(
                {"group_by": "invented"}
            )

    def test_real_execution_persists_computed_registration_summary(
        self,
    ) -> None:
        run, dataset = self.create_run()

        response = self.client.post(
            f"/analysis-runs/{run.id}/execute"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["run"]["status"], "completed")
        self.assertEqual(
            payload["run"]["dataset_version_id"],
            dataset.id,
        )
        self.assertIsNotNone(payload["run"]["started_at"])
        self.assertIsNotNone(payload["run"]["completed_at"])
        self.assertEqual(len(payload["results"]), 1)

        result_payload = payload["results"][0]["payload"]
        self.assertEqual(result_payload["declared_member_count"], 7)
        self.assertEqual(result_payload["grouping_key_count"], 2)
        self.assertEqual(
            result_payload["dataset_version_id"],
            dataset.id,
        )
        self.assertFalse(
            payload["results"][0]["diagnostics"][
                "observation_manifest_inspected"
            ]
        )

        stored = self.db.scalars(select(Result)).all()
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].analysis_run_id, run.id)

    def test_invalid_parameters_fail_before_execution_starts(self) -> None:
        run, _ = self.create_run(
            parameters={"unknown_parameter": True}
        )

        response = self.client.post(
            f"/analysis-runs/{run.id}/execute"
        )

        self.assertEqual(response.status_code, 422)
        self.db.refresh(run)
        self.assertEqual(run.status, "pending")
        self.assertIsNone(run.started_at)
        self.assertEqual(
            self.db.scalars(select(Result)).all(),
            [],
        )

    def test_unknown_executor_is_rejected(self) -> None:
        run, _ = self.create_run(method="unknown_analysis")

        response = self.client.post(
            f"/analysis-runs/{run.id}/execute"
        )

        self.assertEqual(response.status_code, 422)
        self.db.refresh(run)
        self.assertEqual(run.status, "pending")

    def test_executor_failure_records_failed_run_without_result(
        self,
    ) -> None:
        run, _ = self.create_run(method="failing_test_executor")

        with patch.dict(
            EXECUTORS,
            {"failing_test_executor": FailingExecutor()},
        ):
            response = self.client.post(
                f"/analysis-runs/{run.id}/execute"
            )

        self.assertEqual(response.status_code, 500)
        self.db.refresh(run)
        self.assertEqual(run.status, "failed")
        self.assertIsNotNone(run.started_at)
        self.assertIsNotNone(run.completed_at)
        self.assertEqual(
            run.error_message,
            "deterministic executor failure",
        )
        self.assertEqual(
            self.db.scalars(select(Result)).all(),
            [],
        )

    def test_completed_run_cannot_execute_again(self) -> None:
        run, _ = self.create_run()
        first_response = self.client.post(
            f"/analysis-runs/{run.id}/execute"
        )
        second_response = self.client.post(
            f"/analysis-runs/{run.id}/execute"
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(
            len(self.db.scalars(select(Result)).all()),
            1,
        )

    def test_results_endpoint_preserves_run_provenance(self) -> None:
        run, dataset = self.create_run()
        self.client.post(f"/analysis-runs/{run.id}/execute")

        response = self.client.get(
            f"/analysis-runs/{run.id}/results"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["analysis_run_id"], run.id)
        self.assertEqual(
            response.json()[0]["payload"]["dataset_version_id"],
            dataset.id,
        )

    def test_run_dataset_executes_when_plan_dataset_is_unspecified(
        self,
    ) -> None:
        run, dataset = self.create_run(plan_has_dataset=False)

        response = self.client.post(
            f"/analysis-runs/{run.id}/execute"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["run"]["dataset_version_id"],
            dataset.id,
        )
        self.assertEqual(
            response.json()["results"][0]["payload"][
                "dataset_version_id"
            ],
            dataset.id,
        )


if __name__ == "__main__":
    unittest.main()
