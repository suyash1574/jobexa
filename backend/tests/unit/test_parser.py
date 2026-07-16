import pytest
from src.services.parser import DocumentParserService

def test_parse_plain_text():
    text = "  Backend Developer role at Jobexa  "
    result = DocumentParserService.parse_plain_text(text)
    assert result == "Backend Developer role at Jobexa"

def test_parse_pdf():
    # Mock some PDF binary data containing plain text strings
    pdf_data = b"%PDF-1.4\n1 0 obj\n<< /Length 50 >>\nstream\nJob: Software Engineer\nendstream\nendobj"
    result = DocumentParserService.parse_pdf(pdf_data)
    assert "Software Engineer" in result

@pytest.mark.asyncio
async def test_parse_screenshot_ocr_mock(monkeypatch):
    # Mock NIM response when API key is missing
    image_data = b"fakeimagebytes"
    result = await DocumentParserService.parse_screenshot_ocr(image_data)
    assert "Mock OCR text" in result
