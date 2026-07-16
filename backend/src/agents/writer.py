from pydantic import BaseModel, Field
from typing import Optional
from src.agents.base import BaseAgent
from src.agents.planner import ExtractedJobDetails
from src.agents.matcher import MatchResults

class GeneratedApplication(BaseModel):
    email_subject: str = Field(..., description="Finalized professional email subject line")
    email_body: str = Field(..., description="Finalized personalized email body tailored to the recruiter/role")
    cover_letter: Optional[str] = Field(default=None, description="Customized cover letter text if required")

class EmailGenerationAgent(BaseAgent):
    def __init__(self, model_name: str = "meta/llama3-70b-instruct"):
        super().__init__(model_name=model_name)

    async def generate_application(
        self, 
        resume_text: str, 
        job_details: ExtractedJobDetails, 
        match_results: MatchResults,
        user_name: str = "Applicant"
    ) -> GeneratedApplication:
        system_prompt = (
            "You are a professional Email Generation Agent. Write a highly personalized, "
            "professional job application email from the candidate to the recruiter. "
            "Create a compelling, professional subject line. "
            "Write a cover letter that addresses the required skills matching the candidate's experience. "
            "Ensure there is no grammatical errors, the tone is warm but professional, and no placeholder tags remain."
        )
        user_prompt = (
            f"Candidate Name: {user_name}\n"
            f"Candidate Resume: {resume_text}\n\n"
            f"Job Description Details:\n"
            f"Company: {job_details.company_name}\n"
            f"Title: {job_details.job_title}\n"
            f"Recruiter: {job_details.recruiter_email}\n"
            f"Required Skills: {', '.join(job_details.required_skills)}\n\n"
            f"ATS Matching Stats:\n"
            f"Skill Match Score: {match_results.skill_match_score}%\n"
            f"Experience Match Score: {match_results.experience_match_score}%"
        )
        
        try:
            return await self._call_nim(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_schema=GeneratedApplication
            )
        except Exception:
            # Fallback mock application
            return GeneratedApplication(
                email_subject=f"Application for {job_details.job_title} at {job_details.company_name}",
                email_body=(
                    f"Dear Hiring Team,\n\nI am writing to express my strong interest in the {job_details.job_title} "
                    f"position at {job_details.company_name}. Based on my background in Python and FastAPI, I believe "
                    f"I would be a valuable addition to your team.\n\nSincerely,\n{user_name}"
                ),
                cover_letter="Cover letter text placeholder."
            )
