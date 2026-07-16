import pytest
from src.agents.planner import JobAnalysisAgent, ExtractedJobDetails
from src.agents.matcher import ResumeMatchingAgent, MatchResults
from src.agents.writer import EmailGenerationAgent, GeneratedApplication

@pytest.mark.asyncio
async def test_agent_workflow_e2e():
    # 1. Initialize agents
    parser_agent = JobAnalysisAgent()
    matcher_agent = ResumeMatchingAgent()
    writer_agent = EmailGenerationAgent()

    # 2. Run Job Analysis (Mocked behavior or actual depending on key)
    raw_job = "We are hiring a Python Backend Engineer at Google. Requires FastAPI and PostgreSQL. Apply to jobs@google.com"
    job_details = await parser_agent.analyze_job(raw_job)
    assert isinstance(job_details, ExtractedJobDetails)
    assert job_details.company_name is not None
    assert job_details.job_title is not None

    # 3. Run Resume Matching
    resume = "Suyash's Resume: Experienced in Python, FastAPI, and database optimization."
    match_results = await matcher_agent.match_resume(resume, job_details)
    assert isinstance(match_results, MatchResults)
    assert 0 <= match_results.ats_compatibility_score <= 100

    # 4. Run Email/Application Generation
    app_draft = await writer_agent.generate_application(resume, job_details, match_results, user_name="Suyash")
    assert isinstance(app_draft, GeneratedApplication)
    assert app_draft.email_subject is not None
    assert app_draft.email_body is not None
