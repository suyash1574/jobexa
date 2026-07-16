import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from src.main import app
from src.models.base import get_db
from src.api.auth import get_current_user
from src.models.user import User
from src.models.application import ApplicationDraft, JobOpportunity

# Mock dependency overrides
mock_user = User(id=uuid4(), email="test@example.com")

def override_get_current_user():
    return mock_user

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_list_drafts_empty(client, monkeypatch):
    # Mock database query
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def all(self):
            return []
            
    def mock_db_query(self, model):
        return MockQuery()

    from sqlalchemy.orm import Session
    monkeypatch.setattr(Session, "query", mock_db_query)

    response = client.get("/api/v1/drafts")
    assert response.status_code == 200
    assert response.json() == []

def test_get_draft_not_found(client, monkeypatch):
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return None
            
    def mock_db_query(self, model):
        return MockQuery()

    from sqlalchemy.orm import Session
    monkeypatch.setattr(Session, "query", mock_db_query)

    response = client.get(f"/api/v1/drafts/{uuid4()}")
    assert response.status_code == 404
