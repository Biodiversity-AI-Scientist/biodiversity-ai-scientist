import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db, get_dwh_db
from src.llm.contracts import GatewayResult, InvocationMetadata
from src.main import app
from src.models import ResearchProject
from src.schemas.data_intelligence import FeasibilityEvaluationRequest
from src.services import data_intelligence as di_service
from src.services.context import build_brainstorming_context, build_data_intelligence_context, extract_potential_taxa


class DataIntelligenceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 1. In-memory engine for Primary App DB
        cls.app_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.AppSession = sessionmaker(bind=cls.app_engine, expire_on_commit=False)

        # 2. In-memory engine simulating DWH on Server 112
        cls.dwh_engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.DwhSession = sessionmaker(bind=cls.dwh_engine, expire_on_commit=False)

        def override_get_db():
            db = cls.AppSession()
            try:
                yield db
            finally:
                db.close()

        def override_get_dwh_db():
            db = cls.DwhSession()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_dwh_db] = override_get_dwh_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        cls.app_engine.dispose()
        cls.dwh_engine.dispose()

    def setUp(self) -> None:
        Base.metadata.drop_all(self.app_engine)
        Base.metadata.create_all(self.app_engine)
        self.app_db = self.AppSession()

        # Create DWH schema mock tables
        with self.dwh_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS Species;"))
            conn.execute(text("DROP TABLE IF EXISTS TaxonClass;"))
            conn.execute(text("DROP TABLE IF EXISTS ShellRecord;"))
            conn.execute(text("DROP TABLE IF EXISTS ShellImages;"))
            conn.execute(text("DROP TABLE IF EXISTS ImageTransform;"))
            conn.execute(text("DROP TABLE IF EXISTS ImageDatasets;"))
            conn.execute(text("DROP TABLE IF EXISTS ModelInfo;"))
            conn.execute(text("DROP TABLE IF EXISTS ModelNetwork;"))


            conn.execute(
                text(
                    """
                CREATE TABLE TaxonClass (
                    TaxonName VARCHAR(100),
                    TaxonType VARCHAR(50),
                    TaxonParent VARCHAR(100),
                    Family VARCHAR(100),
                    OrderName VARCHAR(100),
                    ClassName VARCHAR(100),
                    Land INT DEFAULT 0,
                    Freshwater INT DEFAULT 0,
                    Brackish INT DEFAULT 0,
                    Marine INT DEFAULT 1,
                    OnlyFossil INT DEFAULT 0
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE Species (
                    SpeciesHash BIGINT,
                    SpeciesGenus VARCHAR(100),
                    SpeciesName VARCHAR(100),
                    AphiaId INT,
                    WORMSStatus VARCHAR(50)
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE ShellRecord (
                    ShellHash BIGINT,
                    SpeciesHash BIGINT,
                    Source VARCHAR(100)
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE ShellImages (
                    ImageHash BIGINT,
                    SpeciesHash BIGINT,
                    ShellHash BIGINT,
                    OrigBaseImage VARCHAR(255)
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE ImageTransform (
                    ID BIGINT PRIMARY KEY,
                    ImageHash BIGINT,
                    SpeciesHash BIGINT,
                    Viewpoint VARCHAR(50),
                    Excluded VARCHAR(1) DEFAULT 'N',
                    category VARCHAR(100)
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE ImageDatasets (
                    ID BIGINT PRIMARY KEY,
                    TransformID BIGINT,
                    Dataset VARCHAR(100),
                    Genus VARCHAR(100),
                    CreateScript VARCHAR(100),
                    CreateDatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UpdateDatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE ModelInfo (
                    ID BIGINT PRIMARY KEY,
                    Taxon VARCHAR(100),
                    Model VARCHAR(255),
                    ViewType VARCHAR(100),
                    CategoryTaxon VARCHAR(100),
                    Accuracy FLOAT,
                    Precision FLOAT,
                    NumTests INT,
                    CreateDatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE ModelNetwork (
                    ID BIGINT PRIMARY KEY,
                    Taxon VARCHAR(200),
                    model VARCHAR(500),
                    ViewType VARCHAR(50),
                    ModelOrderNo INT DEFAULT 0,
                    TaxonLevel VARCHAR(100),
                    TaxonLevelResult VARCHAR(100),
                    IsDefault TINYINT DEFAULT 1,
                    CreateDatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                )
            )

            # Insert sample DWH records
            # Taxa in Strombidae: Canarium, Strombus, Lambis
            conn.execute(
                text(
                    """
                INSERT INTO TaxonClass (TaxonName, TaxonType, TaxonParent, Family, OrderName, ClassName) VALUES
                ('Strombidae', 'Family', 'Littorinimorpha', 'Strombidae', 'Littorinimorpha', 'Gastropoda'),
                ('Canarium', 'Genus', 'Strombidae', 'Strombidae', 'Littorinimorpha', 'Gastropoda'),
                ('Strombus', 'Genus', 'Strombidae', 'Strombidae', 'Littorinimorpha', 'Gastropoda'),
                ('Lambis', 'Genus', 'Strombidae', 'Strombidae', 'Littorinimorpha', 'Gastropoda');
                """
                )
            )

            # Species under Canarium and Strombus
            conn.execute(
                text(
                    """
                INSERT INTO Species (SpeciesHash, SpeciesGenus, SpeciesName, AphiaId, WORMSStatus) VALUES
                (101, 'Canarium', 'urceus', 211111, 'accepted'),
                (102, 'Canarium', 'labiatum', 211112, 'accepted'),
                (103, 'Canarium', 'mutabile', 211113, 'accepted'),
                (104, 'Canarium', 'erythrinum', 211114, 'accepted'),
                (105, 'Strombus', 'alatus', 211115, 'accepted'),
                (106, 'Strombus', 'pugilis', 211116, 'accepted');
                """
                )
            )

            # ShellRecord
            conn.execute(
                text(
                    """
                INSERT INTO ShellRecord (ShellHash, SpeciesHash, Source) VALUES
                (1001, 101, 'Conchology'),
                (1002, 101, 'Gastropods'),
                (1003, 102, 'Conchology'),
                (1004, 103, 'Femorale'),
                (1005, 105, 'Conchology'),
                (1006, 106, 'Gastropods');
                """
                )
            )

            # ShellImages
            conn.execute(
                text(
                    """
                INSERT INTO ShellImages (ImageHash, SpeciesHash, ShellHash, OrigBaseImage) VALUES
                (2001, 101, 1001, 'can_urc_1.jpg'),
                (2002, 101, 1001, 'can_urc_2.jpg'),
                (2003, 101, 1002, 'can_urc_3.jpg'),
                (2004, 102, 1003, 'can_lab_1.jpg'),
                (2005, 103, 1004, 'can_mut_1.jpg'),
                (2006, 105, 1005, 'str_ala_1.jpg'),
                (2007, 105, 1005, 'str_ala_2.jpg'),
                (2008, 106, 1006, 'str_pug_1.jpg'),
                (2009, 106, 1006, 'str_pug_2.jpg');
                """
                )
            )

            # ImageTransform
            conn.execute(
                text(
                    """
                INSERT INTO ImageTransform (ID, ImageHash, SpeciesHash, Viewpoint, Excluded, category) VALUES
                (1, 2001, 101, 'dorsal', 'N', 'urceus'),
                (2, 2002, 101, 'apertural', 'N', 'urceus'),
                (3, 2003, 101, 'dorsal', 'N', 'urceus'),
                (4, 2004, 102, 'dorsal', 'N', 'labiatum'),
                (5, 2005, 103, 'apertural', 'N', 'mutabile'),
                (6, 2006, 105, 'Front', 'N', 'alatus'),
                (7, 2008, 106, 'Front', 'N', 'pugilis');
                """
                )
            )

            # ImageDatasets
            conn.execute(
                text(
                    """
                INSERT INTO ImageDatasets (ID, TransformID, Dataset, Genus, CreateScript) VALUES
                (1, 1, 'genusCanariumDorsal', 'Canarium', 'genusCanariumFront.py'),
                (2, 3, 'genusCanariumDorsal', 'Canarium', 'genusCanariumFront.py'),
                (3, 4, 'genusCanariumDorsal', 'Canarium', 'genusCanariumFront.py');
                """
                )
            )

            # ModelInfo
            conn.execute(
                text(
                    """
                INSERT INTO ModelInfo (ID, Taxon, Model, ViewType, Accuracy, Precision, NumTests) VALUES
                (1, 'Canarium', 'ResNet50_Canarium_v1', 'dorsal', 0.942, 0.938, 120);
                """
                )
            )

            # ModelNetwork
            conn.execute(
                text(
                    """
                INSERT INTO ModelNetwork (ID, Taxon, model, ViewType, TaxonLevel, TaxonLevelResult, IsDefault) VALUES
                (1, 'Strombus', '/Genus_StrombusFront/_training/model_epoch50_Strombus_v1', 'Front', 'GENUS', 'SPECIES', 1),
                (2, 'Strombus', '/Genus_StrombusBack/_training/model_epoch50_Strombus_v1', 'Back', 'GENUS', 'SPECIES', 1),
                (3, 'Strombidae', '/Family_StrombidaeFront/_training/model_epoch50_Strombidae_v1', 'Front', 'FAMILY', 'GENUS', 1);
                """
                )
            )
            conn.commit()



        self.dwh_db = self.DwhSession()

        # Create base test research project
        self.project = ResearchProject(
            title="Strombidae Morphometrics & Biogeography",
            objective="Evaluate evolutionary radiations in family Strombidae.",
            status="draft",
        )
        self.app_db.add(self.project)
        self.app_db.commit()
        self.app_db.refresh(self.project)

    def tearDown(self) -> None:
        self.app_db.close()
        self.dwh_db.close()

    def test_taxon_image_summary_service(self):
        summary = di_service.get_taxon_image_summary(self.dwh_db, "Canarium")
        self.assertEqual(summary.taxon_name, "Canarium")
        self.assertEqual(summary.rank, "Genus")
        self.assertEqual(summary.total_species, 4)
        self.assertEqual(summary.species_with_images, 3)
        self.assertEqual(summary.total_images, 5)
        self.assertIn("dorsal", summary.view_distribution)
        self.assertEqual(summary.view_distribution["dorsal"], 3)
        self.assertEqual(summary.view_distribution["apertural"], 2)
        self.assertIn("Conchology", summary.source_distribution)

    def test_species_image_counts_service(self):
        counts = di_service.get_species_image_counts(self.dwh_db, "Canarium", min_images=2)
        self.assertEqual(len(counts), 4)
        # Urceus has 3 images, so meets_threshold is True
        urceus = next(c for c in counts if c.species_name == "urceus")
        self.assertEqual(urceus.total_images, 3)
        self.assertTrue(urceus.meets_threshold)
        self.assertIn("dorsal", urceus.views)

        # Erythrinum has 0 images
        erythrinum = next(c for c in counts if c.species_name == "erythrinum")
        self.assertEqual(erythrinum.total_images, 0)
        self.assertFalse(erythrinum.meets_threshold)

    def test_genus_image_counts_and_feasibility_service(self):
        genus_counts = di_service.get_genus_image_counts(
            self.dwh_db,
            family_name="Strombidae",
            min_species=2,
            min_images_per_species=1,
        )
        self.assertEqual(len(genus_counts), 2)
        
        canarium = next(g for g in genus_counts if g.genus_name == "Canarium")
        self.assertEqual(canarium.family_name, "Strombidae")
        self.assertEqual(canarium.total_species, 4)
        self.assertEqual(canarium.species_above_threshold, 3)
        self.assertEqual(canarium.total_images, 5)
        self.assertTrue(canarium.is_feasible_for_classifier)
        self.assertFalse(canarium.has_existing_model)

        strombus = next(g for g in genus_counts if g.genus_name == "Strombus")
        self.assertEqual(strombus.total_species, 2)
        self.assertTrue(strombus.has_existing_model)
        self.assertIn("Front", strombus.existing_model_views)
        self.assertIn("Back", strombus.existing_model_views)

    def test_existing_model_networks_service(self):
        models = di_service.get_existing_model_networks(self.dwh_db, taxon_name="Strombus")
        self.assertEqual(len(models), 2)
        views = [m.view_type for m in models]
        self.assertIn("Front", views)
        self.assertIn("Back", views)

        fam_models = di_service.get_existing_model_networks(self.dwh_db, taxon_level="FAMILY")
        self.assertEqual(len(fam_models), 1)
        self.assertEqual(fam_models[0].taxon_name, "Strombidae")

    def test_dataset_class_distribution_service(self):
        dist = di_service.get_dataset_class_distribution(self.dwh_db, "genusCanariumDorsal")
        self.assertEqual(dist.dataset_name, "genusCanariumDorsal")
        self.assertEqual(dist.genus, "Canarium")
        self.assertEqual(dist.total_images, 3)
        self.assertEqual(dist.total_classes, 2)
        self.assertEqual(dist.class_counts["urceus"], 2)
        self.assertEqual(dist.class_counts["labiatum"], 1)
        self.assertEqual(dist.imbalance_ratio, 2.0)

    def test_dataset_source_summary_service(self):
        sources = di_service.get_dataset_source_summary(self.dwh_db, taxon_name="Canarium")
        self.assertGreaterEqual(len(sources), 1)
        source_names = [s.source_name for s in sources]
        self.assertIn("Conchology", source_names)

    def test_existing_dataset_versions_service(self):
        datasets = di_service.get_existing_dataset_versions(self.dwh_db, taxon_name="Canarium")
        self.assertEqual(len(datasets), 1)
        self.assertEqual(datasets[0].dataset_name, "genusCanariumDorsal")
        self.assertEqual(datasets[0].create_script, "genusCanariumFront.py")
        self.assertEqual(datasets[0].total_transforms, 3)

    def test_previous_model_summary_service(self):
        models = di_service.get_previous_model_summary(self.dwh_db, taxon_name="Canarium")
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].model_name, "ResNet50_Canarium_v1")
        self.assertEqual(models[0].accuracy, 0.942)
        self.assertEqual(models[0].precision, 0.938)

    def test_classifier_feasibility_evaluation_service(self):
        req = FeasibilityEvaluationRequest(
            family_name="Strombidae",
            min_species=2,
            min_images_per_species=1,
            max_imbalance_ratio=5.0,
        )
        res = di_service.evaluate_classifier_feasibility(self.dwh_db, req)
        self.assertEqual(res.total_genera_evaluated, 2)
        self.assertIn("Canarium", res.recommended_novel_genera)
        self.assertIn("Strombus", res.recommended_existing_model_genera)

    def test_data_intelligence_rest_endpoints(self):
        # 1. Taxon Summary
        res1 = self.client.get("/data-intelligence/taxon-summary?taxon=Canarium")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["total_images"], 5)

        # 2. Species Counts
        res2 = self.client.get("/data-intelligence/species-counts?genus=Canarium&min_images=1")
        self.assertEqual(res2.status_code, 200)
        self.assertGreaterEqual(len(res2.json()), 3)

        # 3. Genus Counts
        res3 = self.client.get("/data-intelligence/genus-counts?family=Strombidae&min_species=1")
        self.assertEqual(res3.status_code, 200)
        genus_names = [g["genus_name"] for g in res3.json()]
        self.assertIn("Canarium", genus_names)
        self.assertIn("Strombus", genus_names)

        # 4. Dataset Distribution
        res4 = self.client.get("/data-intelligence/dataset-distribution?dataset=genusCanariumDorsal")
        self.assertEqual(res4.status_code, 200)
        self.assertEqual(res4.json()["total_images"], 3)

        # 5. Dataset Sources
        res5 = self.client.get("/data-intelligence/dataset-sources?taxon=Canarium")
        self.assertEqual(res5.status_code, 200)
        self.assertIsInstance(res5.json(), list)

        # 6. Datasets
        res6 = self.client.get("/data-intelligence/datasets?taxon=Canarium")
        self.assertEqual(res6.status_code, 200)
        self.assertEqual(len(res6.json()), 1)

        # 7. Models
        res7 = self.client.get("/data-intelligence/models?taxon=Canarium")
        self.assertEqual(res7.status_code, 200)
        self.assertEqual(res7.json()[0]["accuracy"], 0.942)

        # 8. Model Networks
        res8 = self.client.get("/data-intelligence/model-networks?taxon=Strombus")
        self.assertEqual(res8.status_code, 200)
        self.assertEqual(len(res8.json()), 2)

        # 9. Feasibility POST
        res9 = self.client.post(
            "/data-intelligence/feasibility",
            json={
                "family_name": "Strombidae",
                "min_species": 2,
                "min_images_per_species": 1,
            },
        )
        self.assertEqual(res9.status_code, 200)
        self.assertIn("Canarium", res9.json()["recommended_novel_genera"])
        self.assertIn("Strombus", res9.json()["recommended_existing_model_genera"])


    def test_taxa_extraction_and_data_intelligence_context_builder(self):
        taxa = extract_potential_taxa("Which genus in family Strombidae or genus Canarium is ready?")
        self.assertIn("Strombidae", taxa)
        self.assertIn("Canarium", taxa)

        context_str = build_data_intelligence_context(self.dwh_db, "We want to study Canarium in Strombidae.")
        self.assertIn("Strombidae", context_str)
        self.assertIn("DWH.ModelNetwork", context_str)



    @patch("src.routers.brainstorming_session.LLMGateway")
    def test_brainstorming_turn_receives_ground_truth_dwh_context(self, MockLLMGateway):
        mock_gateway = MagicMock()
        mock_gateway.invoke.return_value = GatewayResult(
            output={
                "reply": "Based on measured DWH material, Canarium has 5 total images with dorsal and apertural views.",
                "suggested_questions": ["What is the dorsal aperture ratio in Canarium?"],
                "candidate_hypotheses": ["Canarium urceus exhibits distinctive dorsal coloration."],
            },
            metadata=InvocationMetadata(
                invocation_id="test-di-inv-1",
                provider="openai_responses",
                model="deepseek-v4-flash",
                template_id="brainstorming_turn_v1",
                schema_id="brainstorming_turn_v1",
                provider_request_id="req-di-1",
                provider_status="completed",
                attempts=1,
                latency_ms=300,
                input_tokens=220,
                output_tokens=100,
                prompt_sha256="p_sha",
                response_sha256="r_sha",
            ),
        )
        MockLLMGateway.return_value = mock_gateway

        # Create brainstorming session
        create_res = self.client.post(
            f"/projects/{self.project.id}/brainstorming-sessions?generate_llm_response=false",
            json={
                "project_id": self.project.id,
                "initial_idea": "Assess feasibility of training a classifier for Canarium in Strombidae.",
            },
        )
        session_id = create_res.json()["id"]

        # Send user message requesting feasibility
        msg_res = self.client.post(
            f"/brainstorming-sessions/{session_id}/messages?generate_llm_response=true",
            json={"content": "Which genus should I train a new classifier for in Strombidae?"},
        )
        self.assertEqual(msg_res.status_code, 200)

        # Verify that gateway.invoke was called and received data_intelligence_context
        called_args = mock_gateway.invoke.call_args
        self.assertEqual(called_args[0][0], "brainstorming_turn_v1")
        input_payload = called_args[1]["inputs"]
        self.assertIsNotNone(input_payload.get("data_intelligence_context"))
        self.assertIn("Canarium", input_payload["data_intelligence_context"])


if __name__ == "__main__":
    unittest.main()
