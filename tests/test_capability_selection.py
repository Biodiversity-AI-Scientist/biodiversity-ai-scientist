import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.database import SessionLocal
from src.llm.contracts import GatewayResult, InvocationMetadata
from src.llm.gateway import LLMGateway
from src.main import app
from src.models.research_project import ResearchProject
from src.models.research_question import ResearchQuestion
from src.models.research_plan import ResearchPlan
from src.models.investigation_step import (
    InvestigationPlanGeneration,
    InvestigationStep,
    InvestigationStepDependency,
)
from src.models.scientific_capability import (
    ScientificApplication,
    ScientificCapability,
    CapabilitySelection,
    CapabilityGap,
)
from src.services.capability_selection import CapabilitySelectionService, compute_step_readiness
from src.schemas.scientific_capability import (
    CapabilitySelectionOverrideRequest,
    CapabilityGapUpdateRequest,
)


class TestCapabilitySelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.client = TestClient(app)

        # Mock LLMGateway.invoke for fast deterministic tests
        cls.patcher = patch.object(LLMGateway, "invoke")
        cls.mock_invoke = cls.patcher.start()

        # 1. Project, Question, Plan, Generation
        cls.project = ResearchProject(
            title="Test Nassarius Project for Phase 9",
            objective="Testing Phase 9 capability matching",
            status="active",
        )
        cls.db.add(cls.project)
        cls.db.commit()

        cls.question = ResearchQuestion(
            project_id=cls.project.id,
            question="Can shell aperture landmarks distinguish Nassarius taxa?",
            status="accepted",
        )
        cls.db.add(cls.question)
        cls.db.commit()

        cls.plan = ResearchPlan(
            project_id=cls.project.id,
            title="Approved Research Plan for Nassarius",
            content={
                "working_title": "Nassarius Plan",
                "research_objective": "Distinguish taxa via aperture morphology",
                "primary_research_question": cls.question.question,
            },
            status="approved",
        )
        cls.db.add(cls.plan)
        cls.db.commit()

        cls.gen = InvestigationPlanGeneration(
            project_id=cls.project.id,
            question_id=cls.question.id,
            research_plan_id=cls.plan.id,
            summary_rationale="DAG for Nassarius shell analysis",
        )
        cls.db.add(cls.gen)
        cls.db.commit()

        # 2. Scientific Applications & Capabilities
        cls.app_worms = ScientificApplication(
            name=f"worms_resolver_{int(datetime.utcnow().timestamp())}",
            display_name="WoRMS Taxa Service",
            category="taxonomy",
            description="WoRMS taxonomic resolution service",
            host_environment="linux_api",
            is_enabled=True,
        )
        cls.db.add(cls.app_worms)
        cls.db.commit()

        cls.cap_worms = ScientificCapability(
            application_id=cls.app_worms.id,
            capability_key=f"worms_taxonomy_lookup_{int(datetime.utcnow().timestamp())}",
            display_name="WoRMS Taxa Resolver",
            scientific_purpose="Verify taxonomic validity and accepted synonymy for marine taxa via WoRMS AphiaID.",
            scientific_tasks="taxonomy_verification",
            is_enabled=True,
        )
        cls.db.add(cls.cap_worms)

        cls.app_ml = ScientificApplication(
            name=f"bio_vision_suite_{int(datetime.utcnow().timestamp())}",
            display_name="Biodiversity Computer Vision Suite",
            category="vision_ml",
            description="Embedding extraction and neural model training",
            host_environment="gpu_cluster",
            is_gpu_required=True,
            is_enabled=True,
        )
        cls.db.add(cls.app_ml)
        cls.db.commit()

        cls.cap_dino = ScientificCapability(
            application_id=cls.app_ml.id,
            capability_key=f"extract_dinov3_embeddings_{int(datetime.utcnow().timestamp())}",
            display_name="DINOv3 Shell Feature Extractor",
            scientific_purpose="Extract 384-dimensional self-supervised vision representations for gastropod shells.",
            scientific_tasks="representation,embedding_extraction",
            is_enabled=True,
        )
        cls.cap_resnet = ScientificCapability(
            application_id=cls.app_ml.id,
            capability_key=f"train_resnet50_classifier_{int(datetime.utcnow().timestamp())}",
            display_name="ResNet-50 Supervised Classifier",
            scientific_purpose="Train 50-layer residual network classifier on shell images.",
            scientific_tasks="classifier,training,classification",
            is_enabled=True,
        )
        cls.db.add_all([cls.cap_dino, cls.cap_resnet])
        cls.db.commit()

        # 3. Investigation Steps
        # Step 1: Taxonomy check (Sole option -> WoRMS)
        cls.step1 = InvestigationStep(
            project_id=cls.project.id,
            question_id=cls.question.id,
            generation_id=cls.gen.id,
            title="Verify Nassarius Taxonomy",
            scientific_goal="Resolve taxon names against WoRMS",
            rationale="Taxonomy standardization",
            step_type="taxonomy",
            requires_capability=True,
            requires_experiment=False,
            required_operation="Lookup Nassarius taxa in WoRMS database",
            display_order=1,
            status="proposed",
        )
        # Step 2: DINOv3 Embeddings (Sole option -> DINOv3)
        cls.step2 = InvestigationStep(
            project_id=cls.project.id,
            question_id=cls.question.id,
            generation_id=cls.gen.id,
            title="Extract Conchological Embeddings",
            scientific_goal="Extract visual representations",
            rationale="Morphological feature extraction",
            step_type="representation",
            requires_capability=True,
            requires_experiment=True,
            required_operation="Extract DINOv3 embeddings on aperture images",
            display_order=2,
            status="proposed",
        )
        # Step 3: Unregistered Exotic Step (Capability Gap)
        cls.step3 = InvestigationStep(
            project_id=cls.project.id,
            question_id=cls.question.id,
            generation_id=cls.gen.id,
            title="Micro-CT 3D Volumetric Reconstruction",
            scientific_goal="Render 3D shell density isosurfaces",
            rationale="Volumetric density analysis",
            step_type="exotic_3d_micro_ct",
            requires_capability=True,
            requires_experiment=True,
            required_operation="Run 3D voxel back-projection from synchrotron x-ray beams",
            display_order=3,
            status="proposed",
        )
        cls.db.add_all([cls.step1, cls.step2, cls.step3])
        cls.db.commit()

        # Add dependency: Step 2 depends on Step 1
        cls.dep = InvestigationStepDependency(
            step_id=cls.step2.id,
            depends_on_step_id=cls.step1.id,
        )
        cls.db.add(cls.dep)
        cls.db.commit()

        # Configure default mock output
        cls.mock_invoke.return_value = GatewayResult(
            output={
                "selected_capability_key": cls.cap_dino.capability_key,
                "scientific_rationale": "DINOv3 provides fine-grained conchological feature representations for gastropods.",
                "rejected_alternatives": [
                    {"capability_key": cls.cap_resnet.capability_key, "rejection_reason": "ResNet requires manual supervised labels."}
                ],
                "known_limitations": "Requires GPU memory >= 16GB",
                "confidence_score": 0.95,
            },
            metadata=InvocationMetadata(
                invocation_id="test-inv-id",
                provider="mock",
                model="gemini-2.5-flash",
                template_id="capability_comparative_selection_v1",
                schema_id="capability_comparative_selection_v1",
                provider_request_id="req-123",
                provider_status="success",
                attempts=1,
                latency_ms=10,
                input_tokens=100,
                output_tokens=50,
                prompt_sha256="abc123sha",
                response_sha256="def456sha",
            ),
        )

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()
        from src.repositories import research_project as repository
        repository.archive_project(cls.db, cls.project.id)
        repository.delete_project(cls.db, cls.project.id)
        cls.db.close()

    def test_01_deterministic_sole_option_matching(self):
        result = CapabilitySelectionService.match_capability_for_step(
            db=self.db,
            step_id=self.step1.id,
        )
        self.assertIsNotNone(result.selected_capability_id)
        self.assertTrue(result.selection_method in ["deterministic_sole_option", "llm_comparative_selection"])
        self.assertIsNotNone(result.scientific_rationale)

    def test_02_capability_gap_generation_when_no_tool_exists(self):
        result = CapabilitySelectionService.match_capability_for_step(
            db=self.db,
            step_id=self.step3.id,
        )
        self.assertIsNone(result.selected_capability_id)
        self.assertEqual(result.selection_method, "none_adequate")

        # Verify CapabilityGap was logged
        gaps = CapabilitySelectionService.list_capability_gaps(
            db=self.db,
            project_id=self.project.id,
        )
        self.assertGreaterEqual(len(gaps), 1)
        matching_gap = next((g for g in gaps if g.investigation_step_id == self.step3.id), None)
        self.assertIsNotNone(matching_gap)
        self.assertEqual(matching_gap.status, "unresolved")
        self.assertIn("Micro-CT", matching_gap.scientific_requirement)

    def test_03_multi_factor_readiness_state(self):
        # Step 1: Capability matched -> ready
        r1, blocked1 = compute_step_readiness(self.db, self.step1)
        self.assertEqual(r1, "ready")
        self.assertFalse(blocked1)

        # Step 2 depends on Step 1 (which is proposed, not completed) -> dependency_blocked
        r2, blocked2 = compute_step_readiness(self.db, self.step2)
        self.assertEqual(r2, "dependency_blocked")
        self.assertTrue(blocked2)

        # Complete Step 1
        self.step1.status = "completed"
        self.db.commit()

        # Step 2 capability not yet matched -> capability_blocked
        r2_after_s1, blocked2_after_s1 = compute_step_readiness(self.db, self.step2)
        self.assertEqual(r2_after_s1, "capability_blocked")
        self.assertTrue(blocked2_after_s1)

        # Match Step 2
        CapabilitySelectionService.match_capability_for_step(self.db, self.step2.id)
        r2_ready, blocked2_ready = compute_step_readiness(self.db, self.step2)
        self.assertEqual(r2_ready, "ready")
        self.assertFalse(blocked2_ready)

    def test_04_human_override_capability_selection(self):
        override_req = CapabilitySelectionOverrideRequest(
            selected_capability_id=self.cap_resnet.id,
            scientific_rationale="Researcher specifically tests ResNet classifier for this step.",
            researcher_status="override",
        )
        override_res = CapabilitySelectionService.override_capability_selection(
            db=self.db,
            step_id=self.step1.id,
            override_req=override_req,
        )
        self.assertEqual(override_res.selected_capability_id, self.cap_resnet.id)
        self.assertEqual(override_res.selection_method, "manual_researcher_selection")
        self.assertEqual(override_res.researcher_status, "override")

    def test_05_capability_gap_resolution_lifecycle(self):
        gaps = CapabilitySelectionService.list_capability_gaps(self.db, self.project.id)
        gap_id = gaps[0].id

        # Update gap to in_progress
        update_req = CapabilityGapUpdateRequest(
            status="in_progress",
            possible_resolution="adapter_development",
            resolution_notes="Building synchrotron 3D reconstruction wrapper adapter.",
        )
        updated_gap = CapabilitySelectionService.update_capability_gap(self.db, gap_id, update_req)
        self.assertEqual(updated_gap.status, "in_progress")

        # Resolve gap
        resolve_req = CapabilityGapUpdateRequest(
            status="resolved",
            resolved=True,
            resolution_notes="Adapter micro_ct_reconstruct registered and validated.",
        )
        resolved_gap = CapabilitySelectionService.update_capability_gap(self.db, gap_id, resolve_req)
        self.assertEqual(resolved_gap.status, "resolved")
        self.assertIsNotNone(resolved_gap.resolved_at)

    def test_06_rest_api_endpoints(self):
        # 1. Match step capability via POST
        res = self.client.post(f"/investigation-steps/{self.step1.id}/capability-selection/match")
        self.assertEqual(res.status_code, 200)
        res_data = res.json()
        self.assertIn("id", res_data)

        # 2. Get selection via GET
        res_get = self.client.get(f"/investigation-steps/{self.step1.id}/capability-selection")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], res_data["id"])

        # 3. Batch match for question
        res_batch = self.client.post(f"/questions/{self.question.id}/capability-selection/match-all")
        self.assertEqual(res_batch.status_code, 200)
        batch_list = res_batch.json()
        self.assertEqual(len(batch_list), 3)

        # 4. List gaps for project
        res_gaps = self.client.get(f"/projects/{self.project.id}/capability-gaps")
        self.assertEqual(res_gaps.status_code, 200)
        self.assertGreaterEqual(len(res_gaps.json()), 1)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "patcher"):
            cls.patcher.stop()
        if hasattr(cls, "db") and cls.db:
            try:
                cls.db.close()
            except Exception:
                pass
        db = SessionLocal()
        try:
            if hasattr(cls, "project") and cls.project:
                step_ids = [s.id for s in db.query(InvestigationStep.id).filter(InvestigationStep.project_id == cls.project.id).all()]
                if step_ids:
                    db.query(InvestigationStepDependency).filter(
                        (InvestigationStepDependency.step_id.in_(step_ids)) |
                        (InvestigationStepDependency.depends_on_step_id.in_(step_ids))
                    ).delete(synchronize_session=False)
                    db.query(CapabilitySelection).filter(CapabilitySelection.investigation_step_id.in_(step_ids)).delete(synchronize_session=False)
                    db.query(InvestigationStep).filter(InvestigationStep.project_id == cls.project.id).delete(synchronize_session=False)
                db.query(CapabilityGap).filter(CapabilityGap.project_id == cls.project.id).delete(synchronize_session=False)
                db.query(InvestigationPlanGeneration).filter(InvestigationPlanGeneration.project_id == cls.project.id).delete(synchronize_session=False)
                db.query(ResearchPlan).filter(ResearchPlan.project_id == cls.project.id).delete(synchronize_session=False)
                db.query(ResearchQuestion).filter(ResearchQuestion.project_id == cls.project.id).delete(synchronize_session=False)
                db.query(ResearchProject).filter(ResearchProject.id == cls.project.id).delete(synchronize_session=False)
            if hasattr(cls, "app_worms") and cls.app_worms:
                w_cap_ids = [c.id for c in db.query(ScientificCapability.id).filter(ScientificCapability.application_id == cls.app_worms.id).all()]
                if w_cap_ids:
                    db.query(CapabilitySelection).filter(CapabilitySelection.selected_capability_id.in_(w_cap_ids)).delete(synchronize_session=False)
                db.query(ScientificCapability).filter(ScientificCapability.application_id == cls.app_worms.id).delete(synchronize_session=False)
                db.query(ScientificApplication).filter(ScientificApplication.id == cls.app_worms.id).delete(synchronize_session=False)
            if hasattr(cls, "app_ml") and cls.app_ml:
                m_cap_ids = [c.id for c in db.query(ScientificCapability.id).filter(ScientificCapability.application_id == cls.app_ml.id).all()]
                if m_cap_ids:
                    db.query(CapabilitySelection).filter(CapabilitySelection.selected_capability_id.in_(m_cap_ids)).delete(synchronize_session=False)
                db.query(ScientificCapability).filter(ScientificCapability.application_id == cls.app_ml.id).delete(synchronize_session=False)
                db.query(ScientificApplication).filter(ScientificApplication.id == cls.app_ml.id).delete(synchronize_session=False)
            db.commit()
        except Exception as e:
            import traceback
            traceback.print_exc()
            db.rollback()
        finally:
            db.close()


