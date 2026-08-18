import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db, get_dwh_db
from src.main import app
from src.models import (
    BrainstormingSession,
    ResearchProject,
)
from src.services.context import build_brainstorming_context

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class CumulativeBrainstormingTestCase(unittest.TestCase):
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

        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        def override_get_dwh_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_dwh_db] = override_get_dwh_db
        self.client = TestClient(app)
        self.db = TestingSessionLocal()

        # Seed project and session
        project = ResearchProject(
            title="Marine Mollusca Cumulative Study",
            objective="Evaluate candidate novel genera for classification models.",
        )
        self.db.add(project)
        self.db.commit()
        self.project_id = project.id

        session = BrainstormingSession(
            project_id=self.project_id,
            initial_idea="What would be a good genus of Mollusca to test cross-genus classification difficulty?",
            status="active",
            messages=[],
        )
        self.db.add(session)
        self.db.commit()
        self.session_id = session.id

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    @patch("src.services.research_program.search_papers_api")
    def test_context_builder_includes_cumulative_science(self, mock_search_papers):
        mock_search_papers.return_value = [
            {
                "paper_id": "test_paper_1",
                "title": "Taxonomic Delimitation in Nassariidae",
                "authors": "Smith et al.",
                "year": 2023,
            }
        ]

        context = build_brainstorming_context(
            db=self.db,
            project_id=self.project_id,
            session_id=self.session_id,
            latest_user_message="Comparing Nassarius vs Chicoreus vs Monetaria",
        )

        data_intel = context.get("data_intelligence_context", "")

        # 1. Verify Research Program Intelligence section is injected
        self.assertIn("RESEARCH PROGRAM INTELLIGENCE (CUMULATIVE SCIENCE)", data_intel)

        # 2. Verify Active Research Agenda items are present
        self.assertIn("ACTIVE RESEARCH PROGRAM AGENDA", data_intel)
        self.assertIn("Cross-Genus Variation in Species Classification Difficulty", data_intel)

        # 3. Verify FindShell Core Methodological Findings are present
        self.assertIn("CORE METHODOLOGICAL FINDINGS FROM FINDSHELL RESEARCH PROGRAM", data_intel)
        self.assertIn("Hierarchical Routing", data_intel)
        self.assertIn("Leakage-Aware & Source-Aware Splitting", data_intel)

        # 4. Verify literature search results from Papers API are included
        self.assertIn("RELEVANT RESEARCH PROGRAM LITERATURE & CITATIONS", data_intel)
        self.assertIn("Taxonomic Delimitation in Nassariidae", data_intel)


if __name__ == "__main__":
    unittest.main()
