import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import MagicMock
from io import BytesIO

from src.main import app
from src.api.auth import get_current_user
from src.models.base import get_db
from src.models.user import User
from src.models.resume import Resume, Certificate
from src.services.storage import StorageService

# Mock user session
mock_user = User(id=uuid4(), email="test@example.com")

def override_get_current_user():
    return mock_user

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_upload_resume_success(client, monkeypatch):
    # 1. Setup mock database session
    db_session_mock = MagicMock()
    def override_get_db():
        yield db_session_mock
    app.dependency_overrides[get_db] = override_get_db

    # 2. Mock StorageService upload_file response
    def mock_upload_file(*args, **kwargs):
        return "https://mock-storage/resumes/resume.pdf"
    monkeypatch.setattr(StorageService, "upload_file", mock_send_email_mock := mock_upload_file)

    # 3. Call endpoint with PDF file bytes
    file_content = b"%PDF-1.4 Mock PDF Data"
    response = client.post(
        "/api/v1/documents/resumes",
        files={"file": ("resume.pdf", BytesIO(file_content), "application/pdf")},
        data={"role_tag": "Backend", "is_default": True}
    )

    # 4. Verify 201 Created and database inserts
    assert response.status_code == 201
    assert response.json()["filename"] == "resume.pdf"
    assert response.json()["file_url"] == "https://mock-storage/resumes/resume.pdf"
    assert db_session_mock.add.called
    assert db_session_mock.commit.called

    app.dependency_overrides.pop(get_db, None)

def test_upload_resume_invalid_format(client):
    # Try uploading a non-PDF file (.txt)
    response = client.post(
        "/api/v1/documents/resumes",
        files={"file": ("resume.txt", BytesIO(b"text file content"), "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

def test_upload_resume_exceeds_size_limit(client, monkeypatch):
    # Mock size limit error inside StorageService
    def mock_upload_file_size_error(*args, **kwargs):
        raise ValueError("File size exceeds the maximum limit of 5MB.")
    monkeypatch.setattr(StorageService, "upload_file", mock_upload_file_size_error)

    # Attempt upload
    response = client.post(
        "/api/v1/documents/resumes",
        files={"file": ("large_resume.pdf", BytesIO(b"%PDF-1.4 Data"), "application/pdf")}
    )
    assert response.status_code == 400
    assert "exceeds the maximum limit" in response.json()["detail"]
