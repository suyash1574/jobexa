import logging
from typing import Optional
import httpx
from src.config import settings

logger = logging.getLogger("jobexa.services.parser")

class DocumentParserService:
    @staticmethod
    def parse_plain_text(text: str) -> str:
        """Simply returns the plain text."""
        return text.strip()

    @staticmethod
    def parse_pdf(pdf_bytes: bytes) -> str:
        """
        Extracts text from PDF bytes.
        For MVP, extracts readable ASCII/UTF-8 strings, or handles via basic parser.
        """
        try:
            # Basic text decoder fallback for ASCII/UTF-8 streams in PDFs
            decoded_text = ""
            # Simple fallback: look for plain text patterns
            decoded_text = pdf_bytes.decode('utf-8', errors='ignore')
            # Extract content between parenthesis if typical PDF stream format, 
            # but for reliability, we can strip out non-printable ASCII
            cleaned_text = "".join(c for c in decoded_text if c.isprintable() or c in "\n\r\t")
            return cleaned_text.strip()
        except Exception as e:
            logger.error(f"Failed parsing PDF: {str(e)}")
            return "Failed to parse PDF content."

    @staticmethod
    async def parse_screenshot_ocr(image_bytes: bytes) -> str:
        """
        Performs OCR on screenshots using an NVIDIA NIM vision-language model.
        """
        if not settings.NVIDIA_NIM_API_KEY or settings.NVIDIA_NIM_API_KEY.startswith("nvapi-aYg1Ir") or "YOUR_KEY" in settings.NVIDIA_NIM_API_KEY:
            logger.warning("NVIDIA NIM API key is missing or mock. Yielding mock OCR text.")
            return "Mock OCR text: Job description details from image."

        # NVIDIA NIM vision-language model endpoint (e.g. llama-3.2-11b-vision-instruct)
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.NVIDIA_NIM_API_KEY}",
            "Content-Type": "application/json"
        }

        # Convert image bytes to base64 data URL
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_image}"

        payload = {
            "model": "meta/llama-3.2-11b-vision-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all readable text from this job posting screenshot. Return only the extracted text."},
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.1
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.error(f"NVIDIA NIM OCR failed: {str(e)}")
                return "Failed to perform OCR on screenshot."
