import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import MagicMock
from src.main import app
from src.api.auth import get_current_user
from src.models.base import get_db
from src.models.user import User
from src.models.application import ApplicationDraft, JobOpportunity
from src.services.email import EmailService

# Mock user with a Telegram Chat ID linked
mock_user = User(id=uuid4(), email="test@example.com", telegram_chat_id="123456789")

def override_get_current_user():
    return mock_user

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_approve_delivery_failure(client, monkeypatch):
    # 1. Setup mock database session and objects
    mock_job = JobOpportunity(
        id=uuid4(),
        company_name="FailCorp",
        job_title="DevOps",
        recruiter_email="recruiting@failcorp.com"
    )
    mock_draft = ApplicationDraft(
        id=uuid4(),
        user_id=mock_user.id,
        job_opportunity_id=mock_job.id,
        email_subject="Apply",
        email_body="Hello",
        job_opportunity=mock_job
    )

    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            # Return our mock objects dynamically
            return mock_draft

    # Mock database session query, add, commit
    db_session_mock = MagicMock()
    db_session_mock.query.return_value = MockQuery()
    
    def override_get_db():
        yield db_session_mock

    app.dependency_overrides[get_db] = override_get_db

    # 2. Force send_application_email_via_gmail to raise exception
    def mock_send_email(*args, **kwargs):
        raise Exception("SMTP Authentication Error: Invalid credentials")

    import src.api.drafts
    monkeypatch.setattr(src.api.drafts, "send_application_email_via_gmail", mock_send_email)

    # 3. Call endpoint
    response = client.post(f"/api/v1/drafts/{mock_draft.id}/approve")
    
    # 4. Verify 502 status code and failed status update in database
    assert response.status_code == 502
    assert "Email dispatch failed" in response.json()["detail"]
    
    # Verify that add was called to store the failed record
    assert db_session_mock.add.called
    added_record = db_session_mock.add.call_args[0][0]
    assert added_record.status == "Failed"
    assert added_record.company_name == "FailCorp"

    # Cleanup overrides
    app.dependency_overrides.pop(get_db, None)
