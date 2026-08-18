import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models.research_project import ResearchProject
from src.services.context import build_brainstorming_context

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class TriGroundedBrainstormingTestCase(unittest.TestCase):
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

        project = ResearchProject(
            title="Marine Nassariidae Morphometrics and Cryptic Complexes",
            objective="Investigating morphological variation and cryptic diversity in the genus Nassarius.",
        )


        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        self.project = project

    def tearDown(self):
        self.db.close()

    def test_context_includes_domain_intelligence(self):
        ctx = build_brainstorming_context(
            db=self.db,
            project_id=self.project.id,
            latest_user_message="Should we build a classifier for Nassarius or Mitra?",
        )
        
        # Verify all 3 intelligence layers are populated
        self.assertIn("data_intelligence_context", ctx)
        self.assertIn("research_program_context", ctx)
        self.assertIn("domain_intelligence_context", ctx)

        full_data_ctx = ctx["data_intelligence_context"]
        self.assertIn("DOMAIN & LITERATURE INTELLIGENCE", full_data_ctx)
        self.assertIn("Nassarius", full_data_ctx)


if __name__ == "__main__":
    unittest.main()
