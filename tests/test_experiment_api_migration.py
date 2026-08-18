import unittest
import logging
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.database import get_db, SessionLocal
from src.models import (
    ResearchProject,
    ResearchQuestion,
    AnalysisPlan,
    AnalysisRun,
    DatasetVersion,
    InvestigationStep,
    ScientificApplication,
    ScientificCapability,
    CapabilitySelection,
)
from src.repositories import research_project as project_repo
from src.telemetry.deprecation import log_legacy_api_access


class TestExperimentApiMigration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        from datetime import datetime, timezone
        ts = int(datetime.now(timezone.utc).timestamp())

        # Create test project
        cls.project = ResearchProject(
            title=f"Migration Test Project {ts}",
            objective="Testing Phase 10A API Migration",
            status="draft",
        )
        cls.db.add(cls.project)
        cls.db.commit()

        # Create test question
        cls.question = ResearchQuestion(
            project_id=cls.project.id,
            question="Can we seamlessly migrate to canonical /experiments endpoints?",
            status="accepted",
        )
        cls.db.add(cls.question)
        cls.db.commit()

        # Create dataset version
        cls.dataset = DatasetVersion(
            project_id=cls.project.id,
            version_key=f"v1_test_migration_{ts}",
            source_system="identifyshell_dwh",
            member_count=50,
        )
        cls.db.add(cls.dataset)
        cls.db.commit()

        # Create app & capability
        cls.app_entity = ScientificApplication(
            name=f"test_mig_suite_{ts}",
            display_name="Migration Test Suite",
            description="Migration test suite description",
            host_environment="server_110",
            category="morphometrics",
            is_enabled=True,
        )
        cls.db.add(cls.app_entity)
        cls.db.commit()

        cls.cap = ScientificCapability(
            application_id=cls.app_entity.id,
            capability_key=f"test_mig_tool_{ts}",
            display_name="Migration Test Tool",
            scientific_purpose="Testing canonical endpoints",
            input_schema={
                "type": "object",
                "properties": {
                    "iterations": {"type": "integer", "minimum": 1, "maximum": 500},
                },
                "required": ["iterations"],
            },
            is_enabled=True,
        )
        cls.db.add(cls.cap)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        project_repo.archive_project(cls.db, cls.project.id)
        project_repo.delete_project(cls.db, cls.project.id)
        cls.db.close()

    def test_01_canonical_experiment_crud_lifecycle(self):
        # 1. Create Experiment via canonical POST /questions/{id}/experiments
        payload = {
            "method": "test_mig_tool",
            "estimand": "Test estimand migration",
            "dataset_version_id": self.dataset.id,
            "parameters": {"iterations": 50},
            "assumptions": {"control": "negative_sample"},
            "exploratory": False,
        }
        res_create = self.client.post(
            f"/questions/{self.question.id}/experiments",
            json=payload,
            headers={"X-Client-Id": "BAIS-AutomatedTests"},
        )
        self.assertEqual(res_create.status_code, 201)
        exp_data = res_create.json()
        exp_id = exp_data["id"]
        self.assertEqual(exp_data["method"], "test_mig_tool")
        self.assertEqual(exp_data["status"], "draft")

        # 2. Get Experiment via canonical GET /experiments/{id}
        res_get = self.client.get(f"/experiments/{exp_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], exp_id)

        # 3. List Experiments for Question via canonical GET /questions/{id}/experiments
        res_list_q = self.client.get(f"/questions/{self.question.id}/experiments")
        self.assertEqual(res_list_q.status_code, 200)
        self.assertGreaterEqual(len(res_list_q.json()), 1)

        # 4. List Experiments for Project via canonical GET /projects/{id}/experiments
        res_list_p = self.client.get(f"/projects/{self.project.id}/experiments")
        self.assertEqual(res_list_p.status_code, 200)
        self.assertGreaterEqual(len(res_list_p.json()), 1)

        # 5. Override Parameters via canonical PUT /experiments/{id}/parameters
        res_override = self.client.put(
            f"/experiments/{exp_id}/parameters",
            json={"parameters": {"iterations": 100}, "justification": "Increased precision"},
        )
        self.assertEqual(res_override.status_code, 200)
        self.assertEqual(res_override.json()["parameters"]["iterations"], 100)

        # 6. Approve Experiment via canonical POST /experiments/{id}/approve
        res_approve = self.client.post(f"/experiments/{exp_id}/approve")
        self.assertEqual(res_approve.status_code, 200)
        self.assertEqual(res_approve.json()["status"], "approved")

    def test_02_canonical_experiment_run_lifecycle(self):
        # Create an experiment first
        exp = AnalysisPlan(
            question_id=self.question.id,
            dataset_version_id=self.dataset.id,
            method="test_mig_tool",
            parameters={"iterations": 20},
            status="approved",
        )
        self.db.add(exp)
        self.db.commit()

        # 1. Create Experiment Run via canonical POST /experiments/{id}/runs
        run_payload = {
            "dataset_version_id": self.dataset.id,
            "tool_name": "test_mig_tool",
            "parameters": {"iterations": 20},
        }
        res_run = self.client.post(
            f"/experiments/{exp.id}/runs",
            json=run_payload,
            headers={"X-Client-Id": "BAIS-WebUI"},
        )
        self.assertEqual(res_run.status_code, 201)
        run_data = res_run.json()
        run_id = run_data["id"]
        self.assertEqual(run_data["status"], "pending")

        # 2. Get Run via canonical GET /experiment-runs/{id}
        res_get_run = self.client.get(f"/experiment-runs/{run_id}")
        self.assertEqual(res_get_run.status_code, 200)
        self.assertEqual(res_get_run.json()["id"], run_id)

        # 3. List Runs for Experiment via canonical GET /experiments/{id}/runs
        res_exp_runs = self.client.get(f"/experiments/{exp.id}/runs")
        self.assertEqual(res_exp_runs.status_code, 200)
        self.assertGreaterEqual(len(res_exp_runs.json()), 1)

        # 4. List Runs for Project via canonical GET /projects/{id}/experiment-runs
        res_proj_runs = self.client.get(f"/projects/{self.project.id}/experiment-runs")
        self.assertEqual(res_proj_runs.status_code, 200)
        self.assertGreaterEqual(len(res_proj_runs.json()), 1)

        # 5. Start Run via canonical POST /experiment-runs/{id}/start
        res_start = self.client.post(f"/experiment-runs/{run_id}/start")
        self.assertEqual(res_start.status_code, 200)
        self.assertEqual(res_start.json()["status"], "running")

        # 6. Complete Run via canonical POST /experiment-runs/{id}/complete
        res_complete = self.client.post(f"/experiment-runs/{run_id}/complete")
        self.assertEqual(res_complete.status_code, 200)
        self.assertEqual(res_complete.json()["status"], "completed")

    def test_03_legacy_shims_delegation_and_telemetry(self):
        # Create an experiment
        exp = AnalysisPlan(
            question_id=self.question.id,
            dataset_version_id=self.dataset.id,
            method="test_mig_tool",
            status="draft",
        )
        self.db.add(exp)
        self.db.commit()

        # Access legacy GET /analysis-plans/{id} with custom X-Client-Id
        with self.assertLogs("bais.telemetry.deprecation", level="WARNING") as log_ctx:
            res_legacy = self.client.get(
                f"/analysis-plans/{exp.id}",
                headers={"X-Client-Id": "LegacyScript_v1.2", "User-Agent": "LegacyPythonClient/1.0"},
            )
            self.assertEqual(res_legacy.status_code, 200)
            self.assertEqual(res_legacy.json()["id"], exp.id)

            # Check that structured telemetry was emitted
            found = False
            for output in log_ctx.output:
                if "legacy_api_deprecation_access" in output and "LegacyScript_v1.2" in output:
                    found = True
                    break
            self.assertTrue(found, "Deprecation telemetry record not found in logs")

        # Test legacy approve shim
        res_app_legacy = self.client.post(
            f"/analysis-plans/{exp.id}/approve",
            headers={"X-Client-Id": "LegacyScript_v1.2"},
        )
        self.assertEqual(res_app_legacy.status_code, 200)
        self.assertEqual(res_app_legacy.json()["status"], "approved")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "db") and cls.db:
            try:
                cls.db.close()
            except Exception:
                pass
        db = SessionLocal()
        try:
            if hasattr(cls, "project") and cls.project:
                proj = db.query(ResearchProject).filter(ResearchProject.id == cls.project.id).first()
                if proj:
                    db.delete(proj)
            if hasattr(cls, "app_entity") and cls.app_entity:
                app_e = db.query(ScientificApplication).filter(ScientificApplication.id == cls.app_entity.id).first()
                if app_e:
                    db.delete(app_e)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


