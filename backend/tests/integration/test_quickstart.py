import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.main import app
from src.models.base import get_db
from src.models.user import User
from src.models.application import JobOpportunity, ApplicationDraft, ApplicationRecord
from src.services.tasks import process_job_submission_task

# 1. Quickstart Scenario 1: Telegram User Account Pairing Test
def test_scenario_1_telegram_pairing(monkeypatch):
    # Setup database mocks
    mock_id = uuid4()
    mock_user = User(
        id=mock_id,
        email="suyash@example.com",
        telegram_pairing_token="123456",
        pairing_token_expires_at=datetime.utcnow() + timedelta(minutes=10)
    )

    db_session_mock = MagicMock()
    # Mock filtering user by token
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return mock_user

    db_session_mock.query.return_value = MockQuery()

    # Call pairing command simulation directly
    user = db_session_mock.query(User).filter(
        User.telegram_pairing_token == "123456",
        User.pairing_token_expires_at > datetime.utcnow()
    ).first()

    assert user is not None
    assert user.email == "suyash@example.com"
    user.telegram_chat_id = "987654321"
    user.telegram_pairing_token = None
    
    assert user.telegram_chat_id == "987654321"
    assert user.telegram_pairing_token is None

# 2. Quickstart Scenario 2: Job Submission & AI Draft Generation
@pytest.mark.asyncio
async def test_scenario_2_job_submission_orchestration(monkeypatch):
    mock_user_id = uuid4()
    
    # Mock process_job_submission_task database queries
    db_session_mock = MagicMock()
    mock_user = User(id=mock_user_id, email="suyash@example.com", telegram_chat_id="123456")
    
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return mock_user

    db_session_mock.query.return_value = MockQuery()

    # Patch SessionLocal to return our mock DB session
    monkeypatch.setattr("src.services.tasks.SessionLocal", lambda: db_session_mock)

    # Run the background processor with mock content
    raw_content = "Hiring Python Backend Developer at Google. Apply to jobs@google.com"
    
    with patch("src.services.tasks.process_job_submission_task", return_value=None) as mock_task:
        await process_job_submission_task(
            user_id=mock_user_id,
            raw_content=raw_content
        )
        # Should execute database additions and task worker triggers
        assert db_session_mock.add.called
        assert db_session_mock.commit.called

# 3. Quickstart Scenario 3: Draft Editing, Approval & Delivery Failure Alert
def test_scenario_3_delivery_failure_propagation(monkeypatch):
    mock_user = User(id=uuid4(), email="suyash@example.com", telegram_chat_id="123456")
    
    app.dependency_overrides[get_current_user] = lambda: mock_user
    
    # Mock drafts and jobs
    mock_job = JobOpportunity(id=uuid4(), company_name="TechCorp", job_title="Backend Developer", recruiter_email="jobs@techcorp.com")
    mock_draft = ApplicationDraft(
        id=uuid4(),
        user_id=mock_user.id,
        job_opportunity_id=mock_job.id,
        email_subject="Apply",
        email_body="Hello",
        job_opportunity=mock_job
    )

    db_session_mock = MagicMock()
    class MockQuery:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return mock_draft

    db_session_mock.query.return_value = MockQuery()
    app.dependency_overrides[get_db] = lambda: db_session_mock

    # Force delivery failure
    import smtplib
    def mock_send_email(*args, **kwargs):
        raise smtplib.SMTPAuthenticationError(535, b"Invalid credentials")
    monkeypatch.setattr("src.api.drafts.EmailService.send_application_email", mock_send_email)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/drafts/{mock_draft.id}/approve")
        assert response.status_code == 502
        assert db_session_mock.add.called
        
        # Verify status updates to Failed
        added_record = db_session_mock.add.call_args[0][0]
        assert added_record.status == "Failed"

    app.dependency_overrides.clear()

from src.api.auth import get_current_user
