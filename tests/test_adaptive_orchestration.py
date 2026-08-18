import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db, get_dwh_db
from src.main import app
from src.models.research_project import ResearchProject
from src.schemas.intelligence_packet import IntelligenceLayer, ResearchIntelligencePacket
from src.services.orchestrator import (
    classify_intelligence_needs,
    assemble_intelligence_packet,
    format_packet_for_llm_prompt,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class AdaptiveOrchestrationTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()
        self.client = TestClient(app)

        project = ResearchProject(
            title="Adaptive Malacology Intelligence Benchmark",
            objective="Testing dynamic intelligence routing across data, program, and domain layers.",
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        self.project = project

    def tearDown(self):
        self.db.close()

    def test_benchmark_1_conceptual_query_routes_to_context_only(self):
        """'What kinds of research could embeddings support?' -> Context only (Zero DB calls)"""
        q = "What kinds of research could embeddings support?"
        layers, rationale = classify_intelligence_needs(q)
        self.assertEqual(layers, set())
        self.assertIn("zero DWH/API", rationale)

    def test_benchmark_2_data_feasibility_routes_to_data_only(self):
        """'Which genus has enough data to train next?' -> Data Intelligence"""
        q = "Which genus has enough data to train next?"
        layers, rationale = classify_intelligence_needs(q)
        self.assertIn(IntelligenceLayer.DATA, layers)
        self.assertNotIn(IntelligenceLayer.DOMAIN, layers)

    def test_benchmark_3_prior_studies_routes_to_data_and_program(self):
        """'Which candidate would best extend previous studies?' -> Data + Program"""
        q = "Which candidate would best extend previous studies and research agenda?"
        layers, rationale = classify_intelligence_needs(q)
        self.assertIn(IntelligenceLayer.DATA, layers)
        self.assertIn(IntelligenceLayer.RESEARCH_PROGRAM, layers)

    def test_benchmark_4_biological_value_routes_to_data_and_domain(self):
        """'Which feasible taxon has the strongest biological research value?' -> Data + Domain"""
        q = "Which feasible taxon has the strongest biological research value and cryptic diversity?"
        layers, rationale = classify_intelligence_needs(q)
        self.assertIn(IntelligenceLayer.DATA, layers)
        self.assertIn(IntelligenceLayer.DOMAIN, layers)

    def test_benchmark_5_major_project_prioritization_routes_to_all_three(self):
        """'Which family should be the next major research project?' -> All 3 layers"""
        q = "Which family should be the next major research project and best candidate to prioritize?"
        layers, rationale = classify_intelligence_needs(q)
        self.assertIn(IntelligenceLayer.DATA, layers)
        self.assertIn(IntelligenceLayer.RESEARCH_PROGRAM, layers)
        self.assertIn(IntelligenceLayer.DOMAIN, layers)

    def test_absence_of_evidence_explicit_flag(self):
        """Missing DWH data must produce explicit absence flag without fabrication."""
        packet = assemble_intelligence_packet(
            db=self.db,
            dwh_db=None,  # Simulated no DWH connection
            project_id=self.project.id,
            user_query="Which genus has available training data?",
        )
        self.assertIsNotNone(packet.data_intelligence)
        self.assertEqual(packet.data_intelligence.status, "no_records")
        
        prompt_text = format_packet_for_llm_prompt(packet)
        self.assertIn("[NO EMPIRICAL RECORDS]", prompt_text)
        self.assertIn("Absence of evidence is explicit", prompt_text)

    def test_four_way_provenance_markers(self):
        """Verify strict formatting of FACT, PREVIOUS FINDING, DOMAIN CLAIM, and LLM INTERPRETATION."""
        packet = assemble_intelligence_packet(
            db=self.db,
            dwh_db=None,
            project_id=self.project.id,
            user_query="Prioritize Nassarius for our next research study",
        )
        prompt_text = format_packet_for_llm_prompt(packet)
        self.assertIn("[PROVENANCE: FACT]", prompt_text)
        self.assertIn("[PROVENANCE: PREVIOUS FINDING]", prompt_text)
        self.assertIn("[PROVENANCE: DOMAIN CLAIM]", prompt_text)
        self.assertIn("[PROVENANCE: LLM INTERPRETATION]", prompt_text)

    def test_orchestrator_route_decision_endpoint(self):
        resp = self.client.post("/orchestrator/route-decision", json={
            "query": "Which candidate would best extend previous studies?"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("data_intelligence", data["activated_layers"])
        self.assertIn("research_program_intelligence", data["activated_layers"])

    def test_orchestrator_inspect_packet_endpoint(self):
        resp = self.client.post("/orchestrator/inspect-packet", json={
            "query": "Should we build a classifier for Nassarius or Vexillum?",
            "project_id": self.project.id,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("packet", data)
        self.assertIn("formatted_prompt", data)
        self.assertIn("Nassarius", data["formatted_prompt"])


if __name__ == "__main__":
    unittest.main()
