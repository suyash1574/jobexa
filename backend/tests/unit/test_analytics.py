import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from src.main import app
from src.api.auth import get_current_user
from src.models.base import get_db
from src.models.user import User
from src.models.application import ApplicationRecord, ApplicationDraft

mock_user = User(id=uuid4(), email="test@example.com")

def override_get_current_user():
    return mock_user

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_dashboard_analytics_mocked(client, monkeypatch):
    # Mock DB counts to return custom stats
    db_session_mock = MagicMock()
    
    # Simulate DB queries returning specific counts
    # We will override db session query count methods
    class MockQuery:
        def __init__(self, count_val=0):
            self.count_val = count_val
            
        def filter(self, *args, **kwargs):
            return self
            
        def count(self):
            return self.count_val

    # Mock different count values based on model queried
    # To keep mock simple, let's mock query directly
    # Total = 10, recent = 5, drafts = 2, interviews = 1, sent = 8
    query_call_count = 0
    def mock_query(model):
        nonlocal query_call_count
        query_call_count += 1
        # Order of queries in get_dashboard_statistics:
        # 1. ApplicationRecord total
        # 2. ApplicationRecord recent
        # 3. ApplicationDraft drafts
        # 4. ApplicationRecord interviews
        # 5. ApplicationRecord sent
        if query_call_count == 1:
            return MockQuery(10)
        elif query_call_count == 2:
            return MockQuery(5)
        elif query_call_count == 3:
            return MockQuery(2)
        elif query_call_count == 4:
            return MockQuery(1)
        else:
            return MockQuery(8)

    db_session_mock.query = mock_query

    def override_get_db():
        yield db_session_mock

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_applications"] == 10
    assert data["applications_this_month"] == 5
    assert data["pending_drafts"] == 2
    assert data["interviews"] == 1
    assert data["response_rate"] == 90.0 # (1 interview + 8 offers) / 10 * 100

    app.dependency_overrides.pop(get_db, None)

from unittest.mock import MagicMock
