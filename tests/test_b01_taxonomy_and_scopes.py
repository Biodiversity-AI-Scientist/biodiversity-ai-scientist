"""
Automated Test Suite for Phase B01 v3:
Biodiversity Capability Taxonomy, Implementation-Level 4-Tier Scope Governance,
Two-Tier Data Model (CapabilityImplementation), Canonical Semantic Contracts,
and Reconciled 14-Domain Coverage Matrix.
"""
import unittest
from fastapi.testclient import TestClient

from src.core.contracts.semantic_types import (
    BIODIVERSITY_DOMAINS,
    SEMANTIC_DATA_TYPES,
    AvailabilityStatus,
    BiodiversityDomain,
    CapabilityScope,
    KnowledgeStatus,
    ScientificMaturity,
)
from src.database import SessionLocal
from src.main import app
from src.services.taxonomy_seed import seed_biodiversity_taxonomy


class TestB01BiodiversityTaxonomyAndScopes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_semantic_types_catalogue_contract(self):
        response = self.client.get("/capabilities/semantic-types")
        self.assertEqual(response.status_code, 200)
        types_data = response.json()

        self.assertGreaterEqual(len(types_data), 14)
        type_keys = {item["type_key"] for item in types_data}
        expected_types = [
            "occurrence_dataset_v1",
            "specimen_image_collection_v1",
            "dense_feature_embedding_v1",
            "taxonomic_backbone_v1",
            "morphological_trait_table_v1",
            "range_polygon_manifest_v1",
            "phylogenetic_tree_v1",
            "community_abundance_matrix_v1",
            "genetic_distance_matrix_v1",
            "population_time_series_v1",
            "environmental_raster_v1",
            "asv_table_v1",
            "interaction_network_v1",
            "spatial_metric_result_v1",
        ]
        for t in expected_types:
            self.assertIn(t, type_keys)

        # Check machine-validatable attributes on occurrence_dataset_v1
        occ_type = next(t for t in types_data if t["type_key"] == "occurrence_dataset_v1")
        self.assertIn("occurrence_id", occ_type["required_fields"])
        self.assertIn("scientific_name", occ_type["required_fields"])
        self.assertTrue(len(occ_type["validation_rules"]) > 0)

        # Check unique primary identifiers for datasets/matrices
        trait_type = next(t for t in types_data if t["type_key"] == "morphological_trait_table_v1")
        self.assertIn("trait_observation_id", trait_type["required_fields"])

        comm_type = next(t for t in types_data if t["type_key"] == "community_abundance_matrix_v1")
        self.assertIn("matrix_id", comm_type["required_fields"])

        time_type = next(t for t in types_data if t["type_key"] == "population_time_series_v1")
        self.assertIn("observation_id", time_type["required_fields"])

    def test_02_seed_taxonomy_and_14_normalized_domains(self):
        seed_res = self.client.post("/capabilities/seed-taxonomy")
        self.assertEqual(seed_res.status_code, 200)
        seed_data = seed_res.json()
        self.assertIn("total_capabilities", seed_data)
        self.assertIn("total_implementations", seed_data)

        domains_res = self.client.get("/capabilities/domains")
        self.assertEqual(domains_res.status_code, 200)
        domains_data = domains_res.json()
        self.assertEqual(len(domains_data), 14)

        domain_keys = {d["domain"] for d in domains_data}
        for d_enum in BiodiversityDomain:
            self.assertIn(d_enum.value, domain_keys)

        dom_map = {d["domain"]: d["display_name"] for d in domains_data}
        self.assertEqual(dom_map["species_populations"], "Species Populations & Occurrence")
        self.assertEqual(dom_map["species_traits"], "Species Traits & Morphology")
        self.assertEqual(dom_map["genetic_composition"], "Genetic Composition & Diversity")

    def test_03_implementation_level_scope_governance(self):
        seed_biodiversity_taxonomy(self.db)

        # Retrieve all capabilities with implementations
        res = self.client.get("/capabilities")
        self.assertEqual(res.status_code, 200)
        caps = res.json()

        # Find extract_image_embeddings
        embed_cap = next((c for c in caps if c["capability_key"] == "extract_image_embeddings"), None)
        self.assertIsNotNone(embed_cap)
        # Abstract capability is generic method
        self.assertTrue(embed_cap["is_generic"])
        # But implementations have distinct deployment scopes
        impls = embed_cap.get("implementations", [])
        self.assertGreaterEqual(len(impls), 2)

        dinov3_impl = next(i for i in impls if i["implementation_key"] == "identifyshell_dinov3_v1")
        self.assertEqual(dinov3_impl["implementation_scope"], "identifyshell_specific")

        bioclip_impl = next(i for i in impls if i["implementation_key"] == "bioclip_adapter_v1")
        self.assertEqual(bioclip_impl["implementation_scope"], "official_extension")

    def test_04_metadata_contracts_preconditions_and_evidence(self):
        seed_biodiversity_taxonomy(self.db)

        res = self.client.get("/capabilities?domain=biogeography_macroecology")
        self.assertEqual(res.status_code, 200)
        caps = res.json()
        self.assertGreaterEqual(len(caps), 1)

        eoo_cap = next((c for c in caps if "extent_of_occurrence" in c["capability_key"]), caps[0])
        self.assertIsNotNone(eoo_cap.get("preconditions"))
        self.assertIsNotNone(eoo_cap.get("scientific_assumptions"))
        self.assertIsNotNone(eoo_cap.get("expected_evidence_types"))
        self.assertTrue(len(eoo_cap["expected_evidence_types"]) > 0)

        # Check embedding capability evidence semantics (Result/Artifact, not scientific evidence)
        res_traits = self.client.get("/capabilities?domain=species_traits")
        self.assertEqual(res_traits.status_code, 200)
        traits_caps = res_traits.json()
        embed_cap = next((c for c in traits_caps if c["capability_key"] == "extract_image_embeddings"), None)
        self.assertIsNotNone(embed_cap)
        self.assertEqual(embed_cap.get("expected_evidence_types"), [])

    def test_05_two_tier_abstraction_model_and_1_to_n_implementations(self):
        seed_biodiversity_taxonomy(self.db)

        res = self.client.get("/capabilities")
        self.assertEqual(res.status_code, 200)
        caps = res.json()

        embed_cap = next((c for c in caps if c["capability_key"] == "extract_image_embeddings"), None)
        self.assertIsNotNone(embed_cap)
        self.assertIn("implementations", embed_cap)
        self.assertGreaterEqual(len(embed_cap["implementations"]), 2)

        impl_keys = {im["implementation_key"] for im in embed_cap["implementations"]}
        self.assertIn("identifyshell_dinov3_v1", impl_keys)
        self.assertIn("bioclip_adapter_v1", impl_keys)

    def test_06_decomposed_maturity_model_and_availability_filtering(self):
        seed_biodiversity_taxonomy(self.db)

        inst_res = self.client.get("/capabilities?availability=installed")
        self.assertEqual(inst_res.status_code, 200)
        inst_caps = inst_res.json()
        self.assertGreaterEqual(len(inst_caps), 5)

        val_res = self.client.get("/capabilities?knowledge_status=validated")
        self.assertEqual(val_res.status_code, 200)
        val_caps = val_res.json()
        self.assertGreaterEqual(len(val_caps), 3)

    def test_07_biodiversity_coverage_matrix_reconciliation(self):
        seed_biodiversity_taxonomy(self.db)

        res = self.client.get("/capabilities/coverage-matrix")
        self.assertEqual(res.status_code, 200)
        matrix = res.json()

        self.assertIn("domains", matrix)
        self.assertEqual(len(matrix["domains"]), 14)
        
        # Verify 100% mathematical reconciliation between row sums and total metrics
        calc_known = sum(d["known_specs_count"] for d in matrix["domains"])
        calc_inst = sum(d["installed_count"] for d in matrix["domains"])
        calc_val = sum(d["validated_count"] for d in matrix["domains"])
        calc_ext = sum(d["extension_count"] for d in matrix["domains"])
        calc_extern = sum(d["external_count"] for d in matrix["domains"])
        calc_gaps = sum(d["gap_count"] for d in matrix["domains"])

        self.assertEqual(matrix["total_known_specs"], calc_known)
        self.assertEqual(matrix["total_installed"], calc_inst)
        self.assertEqual(matrix["total_validated"], calc_val)
        self.assertEqual(matrix["total_extensions"], calc_ext)
        self.assertEqual(matrix["total_external"], calc_extern)
        self.assertEqual(matrix["total_gaps"], calc_gaps)

    def test_08_canonical_contracts_and_spatial_crs(self):
        from src.core.contracts.semantic_types import SEMANTIC_DATA_TYPES

        # 1. Spatial types require CRS
        occ = SEMANTIC_DATA_TYPES["occurrence_dataset_v1"]
        self.assertIsNotNone(occ.crs)
        self.assertIn("EPSG:4326", occ.crs)

        polygon = SEMANTIC_DATA_TYPES["range_polygon_manifest_v1"]
        self.assertIsNotNone(polygon.crs)

        # 2. Non-spatial types must not mandate CRS
        tree = SEMANTIC_DATA_TYPES["phylogenetic_tree_v1"]
        self.assertIsNone(tree.crs)

        asv = SEMANTIC_DATA_TYPES["asv_table_v1"]
        self.assertIsNone(asv.crs)

        emb = SEMANTIC_DATA_TYPES["dense_feature_embedding_v1"]
        self.assertIsNone(emb.crs)

        gen_dist = SEMANTIC_DATA_TYPES["genetic_distance_matrix_v1"]
        self.assertIsNone(gen_dist.crs)


if __name__ == "__main__":
    unittest.main()
