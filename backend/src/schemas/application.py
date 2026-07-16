from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime, date
from typing import List, Optional

class JobOpportunityBase(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    recruiter_email: Optional[str] = None
    application_deadline: Optional[date] = None
    original_source_url: Optional[str] = None

class JobOpportunityOut(JobOpportunityBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationDraftBase(BaseModel):
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    cover_letter: Optional[str] = None
    recommended_resume_id: Optional[UUID] = None
    recommended_certificate_ids: List[UUID] = []
    ats_compatibility_score: int = 0
    skill_match_score: int = 0
    experience_match_score: int = 0
    status: str = "Draft"

class ApplicationDraftOut(ApplicationDraftBase):
    id: UUID
    user_id: UUID
    job_opportunity_id: UUID
    job_opportunity: Optional[JobOpportunityOut] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApplicationDraftUpdate(BaseModel):
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    cover_letter: Optional[str] = None
    recommended_resume_id: Optional[UUID] = None
    recommended_certificate_ids: Optional[List[UUID]] = None
    status: Optional[str] = None

class ApplicationRecordOut(BaseModel):
    id: UUID
    user_id: UUID
    company_name: str
    position: str
    date_applied: datetime
    email_sent_body: str
    email_subject: str
    sent_resume_url: str
    sent_certificate_urls: List[str] = []
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
