import unittest
from fastapi.testclient import TestClient

from src.main import app
from src.database import SessionLocal
from src.models.scientific_capability import ScientificApplication, ScientificCapability


class TestCapabilityRegistry(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_list_applications(self):
        response = self.client.get("/applications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

        # Check Studio Model Pipeline is present
        studio_app = next((a for a in data if a["name"] == "studio_model_pipeline"), None)
        self.assertIsNotNone(studio_app)
        self.assertEqual(studio_app["is_gpu_required"], True)
        self.assertEqual(studio_app["invocation_type"], "manual_web_ui")
        self.assertIn("pipeline/index.php", studio_app["interface_url"])

    def test_list_capabilities_and_filter(self):
        response = self.client.get("/capabilities")
        self.assertEqual(response.status_code, 200)
        caps = response.json()
        self.assertIsInstance(caps, list)
        self.assertGreaterEqual(len(caps), 4)

        # Test filter by category
        vision_res = self.client.get("/capabilities?category=vision_ml")
        self.assertEqual(vision_res.status_code, 200)
        vision_caps = vision_res.json()
        for c in vision_caps:
            self.assertEqual(c["creates_result"], True)

    def test_create_application_and_capability(self):
        unique_name = "test_custom_morpho_app"
        # Clean up if exists
        existing = self.db.query(ScientificApplication).filter_by(name=unique_name).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()

        app_payload = {
            "name": unique_name,
            "display_name": "Custom Morpho Analyzer",
            "category": "statistics",
            "description": "Test morpho analyzer tool",
            "host_environment": "Local Host",
            "invocation_type": "cli_script",
            "is_gpu_required": False,
            "capabilities": [
                {
                    "capability_key": "test_fourier_contour_analysis",
                    "display_name": "Elliptic Fourier Contour Analysis",
                    "scientific_purpose": "Quantify closed shell outline harmonics",
                    "typical_duration": "5 seconds",
                    "reproducibility_level": "deterministic",
                    "modifies_data": False,
                    "default_parameters": {"harmonics": 20}
                }
            ]
        }

        res = self.client.post("/applications", json=app_payload)
        self.assertEqual(res.status_code, 201)
        created_app = res.json()
        self.assertEqual(created_app["name"], unique_name)
        self.assertEqual(len(created_app["capabilities"]), 1)

        cap_id = created_app["capabilities"][0]["id"]
        cap_res = self.client.get(f"/capabilities/{cap_id}")
        self.assertEqual(cap_res.status_code, 200)
        self.assertEqual(cap_res.json()["capability_key"], "test_fourier_contour_analysis")

        # Test Patch / Toggle
        patch_res = self.client.patch(f"/capabilities/{cap_id}", json={"is_enabled": False, "display_name": "Updated Morpho"})
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["is_enabled"], False)
        self.assertEqual(patch_res.json()["display_name"], "Updated Morpho")

        # Cleanup
        app_in_db = self.db.query(ScientificApplication).filter_by(name=unique_name).first()
        if app_in_db:
            self.db.delete(app_in_db)
            self.db.commit()

    def test_capabilities_context_helper(self):
        from src.services.context import build_capabilities_summary
        summary = build_capabilities_summary(self.db)
        self.assertIn("AVAILABLE REGISTERED SCIENTIFIC CAPABILITIES", summary)
        self.assertIn("studio_dinov3_embedding_extraction", summary)


if __name__ == "__main__":
    unittest.main()

