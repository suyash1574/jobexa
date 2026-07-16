from pydantic import BaseModel, Field
from typing import List, Optional
from src.agents.base import BaseAgent

class ExtractedJobDetails(BaseModel):
    company_name: Optional[str] = Field(default=None, description="Extracted company name")
    job_title: Optional[str] = Field(default=None, description="Extracted job title/role")
    required_skills: List[str] = Field(default=[], description="List of required skills")
    preferred_skills: List[str] = Field(default=[], description="List of preferred/nice-to-have skills")
    recruiter_email: Optional[str] = Field(default=None, description="Extracted recruiter email address")
    application_deadline: Optional[str] = Field(default=None, description="Extracted deadline date in YYYY-MM-DD format")
    original_source_url: Optional[str] = Field(default=None, description="Original source job board URL if found")

class JobAnalysisAgent(BaseAgent):
    def __init__(self, model_name: str = "meta/llama3-70b-instruct"):
        super().__init__(model_name=model_name)

    async def analyze_job(self, raw_text: str) -> ExtractedJobDetails:
        system_prompt = (
            "You are a Job Description Analysis Agent. Your task is to extract structured details from the "
            "raw job posting text. Pay close attention to extracting the recruiter email, required skills, "
            "and preferred skills."
        )
        user_prompt = f"Analyze this raw job opportunity content:\n\n{raw_text}"
        
        try:
            return await self._call_nim(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=ExtractedJobDetails
            )
        except Exception:
            # Fallback mock for testing in case of errors
            return ExtractedJobDetails(
                company_name="TechCorp",
                job_title="Software Engineer",
                required_skills=["Python", "FastAPI"],
                preferred_skills=["Docker"],
                recruiter_email=None
            )
