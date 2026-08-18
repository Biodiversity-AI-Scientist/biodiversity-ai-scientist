import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.domain_intelligence import WormsTaxonomicRecord, TaxonBiologicalContext
from src.services.domain_intelligence import (
    fetch_worms_record,
    get_taxon_domain_intelligence,
    format_domain_intelligence_for_prompt,
)


class DomainIntelligenceTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("src.services.domain_intelligence.httpx.Client")
    def test_worms_record_parsing(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        
        # Mock main record response
        mock_resp_main = MagicMock()
        mock_resp_main.status_code = 200
        mock_resp_main.json.return_value = [{
            "AphiaID": 138235,
            "scientificname": "Nassarius",
            "authority": "Duméril, 1805",
            "rank": "Genus",
            "status": "accepted",
            "family": "Nassariidae",
            "order": "Neogastropoda",
            "class": "Gastropoda",
            "phylum": "Mollusca",
            "kingdom": "Animalia",
            "isMarine": 1,
        }]

        # Mock synonyms response
        mock_resp_syn = MagicMock()
        mock_resp_syn.status_code = 200
        mock_resp_syn.json.return_value = [
            {"scientificname": "Arcularia"},
            {"scientificname": "Nassa"},
        ]

        def get_side_effect(url, **kwargs):
            if "AphiaRecordsByName" in url:
                return mock_resp_main
            return mock_resp_syn

        mock_client.get.side_effect = get_side_effect

        record = fetch_worms_record("MockNassarius")
        self.assertIsNotNone(record)
        self.assertEqual(record.scientific_name, "Nassarius")
        self.assertEqual(record.status, "accepted")
        self.assertEqual(record.family, "Nassariidae")
        self.assertIn("Arcularia", record.synonyms)

    def test_domain_intelligence_aggregation(self):
        ctx = get_taxon_domain_intelligence("Nassarius")
        self.assertEqual(ctx.taxon_name, "Nassarius")
        self.assertTrue(ctx.has_cryptic_complexes)
        self.assertGreaterEqual(len(ctx.morphological_challenges), 1)

        formatted = format_domain_intelligence_for_prompt(ctx)
        self.assertIn("Nassarius", formatted)
        self.assertIn("Cryptic Diversity", formatted)

    def test_compare_taxa_priorities_endpoint(self):
        resp = self.client.post("/taxa/compare-priorities", json={
            "taxon_a": "Nassarius",
            "taxon_b": "Vexillum",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("recommended_priority", data)
        self.assertIn("justification", data)
        self.assertIn("comparative_dimensions", data)

    def test_get_biological_context_endpoint(self):
        resp = self.client.get("/taxa/Nassarius/biological-context")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["taxon_name"], "Nassarius")
        self.assertTrue(data["has_cryptic_complexes"])

    @patch("src.services.domain_intelligence.httpx.Client")
    def test_biorxiv_literature_search(self, mock_client_cls):
        from src.services.domain_intelligence import search_biorxiv_literature
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {
                "items": [{
                    "title": ["Cryptic Speciation in Marine Mollusks"],
                    "DOI": "10.1101/2026.01.01.123456",
                    "author": [{"given": "Jane", "family": "Doe"}],
                    "created": {"date-parts": [[2026, 1, 1]]},
                }]
            }
        }
        mock_client.get.return_value = mock_resp

        results = search_biorxiv_literature("MockMollusk", max_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source, "bioRxiv (Biology & Biodiversity)")
        self.assertEqual(results[0].doi, "10.1101/2026.01.01.123456")



if __name__ == "__main__":
    unittest.main()
