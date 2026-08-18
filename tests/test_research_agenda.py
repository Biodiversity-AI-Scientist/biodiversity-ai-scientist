import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db, get_dwh_db
from src.main import app
from src.models.research_agenda import ResearchAgendaItem
from src.repositories.research_agenda import (
    create_agenda_item,
    get_agenda_item,
    list_agenda_items,
    seed_default_research_agenda_if_empty,
    update_agenda_item,
)
from src.schemas.research_agenda import (
    ResearchAgendaItemCreate,
    ResearchAgendaItemUpdate,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


class ResearchAgendaTestCase(unittest.TestCase):
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

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def test_seed_default_research_agenda(self):
        # Initial count should be 0
        self.assertEqual(self.db.query(ResearchAgendaItem).count(), 0)

        # Seed items
        count = seed_default_research_agenda_if_empty(self.db)
        self.assertEqual(count, 8)
        self.assertEqual(self.db.query(ResearchAgendaItem).count(), 8)

        # Second seeding call should be a no-op (idempotent)
        count_again = seed_default_research_agenda_if_empty(self.db)
        self.assertEqual(count_again, 0)

    def test_create_and_get_agenda_item(self):
        item = create_agenda_item(
            db=self.db,
            item_data=ResearchAgendaItemCreate(
                title="Few-Shot Morphometrics in Cypraea",
                description="Testing few-shot learning thresholds on tiger cowries.",
                type="research_opportunity",
                status="investigating",
                current_evidence="Pretrained ResNet requires >=20 samples per species.",
                follow_up_opportunities="Test on Cypraea tigris and Cypraea pantherina.",
            ),
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(item.title, "Few-Shot Morphometrics in Cypraea")
        self.assertEqual(item.type, "research_opportunity")

        fetched = get_agenda_item(self.db, item.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Few-Shot Morphometrics in Cypraea")

    def test_list_agenda_items_with_filters(self):
        seed_default_research_agenda_if_empty(self.db)

        # List all
        all_items = list_agenda_items(self.db)
        self.assertEqual(len(all_items), 8)

        # Filter by status
        open_items = list_agenda_items(self.db, status_filter="open")
        for it in open_items:
            self.assertEqual(it.status, "open")

        # Filter by type
        method_items = list_agenda_items(self.db, type_filter="methodological_issue")
        for it in method_items:
            self.assertEqual(it.type, "methodological_issue")

    def test_update_agenda_item_status(self):
        item = create_agenda_item(
            db=self.db,
            item_data=ResearchAgendaItemCreate(
                title="Test update",
                description="Test description",
                type="open_question",
                status="open",
            ),
        )
        updated = update_agenda_item(
            db=self.db,
            item=item,
            update_data=ResearchAgendaItemUpdate(
                status="resolved",
                current_evidence="Resolved in follow-up experiment.",
            ),
        )
        self.assertEqual(updated.status, "resolved")
        self.assertEqual(updated.current_evidence, "Resolved in follow-up experiment.")

    def test_rest_endpoints(self):
        # 1. GET /research-agenda (auto-seeds if empty)
        res = self.client.get("/research-agenda")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data), 8)

        # 2. POST /research-agenda
        post_res = self.client.post(
            "/research-agenda",
            json={
                "title": "REST API Agenda Item",
                "description": "Created via FastAPI router",
                "type": "limitation",
                "status": "open",
            },
        )
        self.assertEqual(post_res.status_code, 201)
        new_id = post_res.json()["id"]

        # 3. GET /research-agenda/{id}
        get_res = self.client.get(f"/research-agenda/{new_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["title"], "REST API Agenda Item")

        # 4. PATCH /research-agenda/{id}
        patch_res = self.client.patch(
            f"/research-agenda/{new_id}",
            json={"status": "investigating"},
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "investigating")

        # 5. GET /research-program/publications
        pub_res = self.client.get("/research-program/publications")
        self.assertEqual(pub_res.status_code, 200)
        self.assertIn("publications", pub_res.json())


if __name__ == "__main__":
    unittest.main()
