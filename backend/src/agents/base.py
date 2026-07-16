import httpx
import logging
from typing import Type, TypeVar
from pydantic import BaseModel
from src.config import settings

logger = logging.getLogger("jobexa.agents")

T = TypeVar("T", bound=BaseModel)

class BaseAgent:
    def __init__(self, model_name: str = "meta/llama3-70b-instruct"):
        self.model_name = model_name
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.api_key = settings.NVIDIA_NIM_API_KEY

    async def _call_nim(self, system_prompt: str, user_prompt: str, response_schema: Type[T]) -> T:
        if not self.api_key or self.api_key.startswith("nvapi-aYg1Ir") or "YOUR_KEY" in self.api_key:
            # Fallback mock or error based on setting
            logger.warning("NVIDIA NIM API key is missing. Yielding default mocked data.")
            schema_name = response_schema.__name__
            if schema_name == "ExtractedJobDetails":
                return response_schema(
                    company_name="Google",
                    job_title="Backend Engineer",
                    required_skills=["Python", "FastAPI"],
                    preferred_skills=["PostgreSQL"],
                    recruiter_email="jobs@google.com"
                )
            elif schema_name == "MatchResults":
                return response_schema(
                    ats_compatibility_score=85,
                    skill_match_score=90,
                    experience_match_score=80
                )
            elif schema_name == "GeneratedApplication":
                return response_schema(
                    email_subject="Application for Backend Engineer",
                    email_body="Dear Hiring Team,\n\nI am writing to apply...",
                    cover_letter="Cover letter text"
                )
            # Create a mock instance with defaults for testing if key is absent
            return response_schema.model_validate(response_schema.model_construct().model_dump())

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Request structured output using tool definitions or prompt instruction
        # NVIDIA NIM standard format supports JSON response mode
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt + "\nIMPORTANT: Return ONLY a raw JSON object that strictly conforms to the requested schema. Do not enclose in markdown block quotes or add conversational filler."},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                return response_schema.model_validate_json(content)
            except Exception as e:
                logger.error(f"NVIDIA NIM call failed: {str(e)}")
                raise e
