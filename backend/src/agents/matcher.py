from pydantic import BaseModel, Field
from src.agents.base import BaseAgent
from src.agents.planner import ExtractedJobDetails

class MatchResults(BaseModel):
    ats_compatibility_score: int = Field(default=75, ge=0, le=100, description="Overall ATS compatibility match percentage (0-100)")
    skill_match_score: int = Field(default=70, ge=0, le=100, description="Skill overlap match percentage (0-100)")
    experience_match_score: int = Field(default=80, ge=0, le=100, description="Experience alignment match percentage (0-100)")

class ResumeMatchingAgent(BaseAgent):
    def __init__(self, model_name: str = "meta/llama3-70b-instruct"):
        super().__init__(model_name=model_name)

    async def match_resume(self, resume_text: str, job_details: ExtractedJobDetails) -> MatchResults:
        system_prompt = (
            "You are an ATS Resume Matching Agent. Compare the candidate's resume against the "
            "job description required and preferred skills. Calculate the ATS compatibility score, "
            "skill match score, and experience match score as percentages (0 to 100)."
        )
        user_prompt = (
            f"Candidate Resume Content:\n{resume_text}\n\n"
            f"Job Opportunities Details:\n"
            f"Title: {job_details.job_title}\n"
            f"Required Skills: {', '.join(job_details.required_skills)}\n"
            f"Preferred Skills: {', '.join(job_details.preferred_skills)}\n"
        )
        
        try:
            return await self._call_nim(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=MatchResults
            )
        except Exception:
            return MatchResults()
