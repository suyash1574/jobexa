from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey, Text, Boolean, Uuid, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from src.models.base import Base

class JobOpportunity(Base):
    __tablename__ = "job_opportunities"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    required_skills = Column(JSON, nullable=False, default=list)
    preferred_skills = Column(JSON, nullable=False, default=list)
    recruiter_email = Column(String, nullable=True)
    application_deadline = Column(Date, nullable=True)
    raw_content = Column(Text, nullable=False)
    original_source_url = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    drafts = relationship("ApplicationDraft", back_populates="job_opportunity", cascade="all, delete-orphan")

class ApplicationDraft(Base):
    __tablename__ = "application_drafts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_opportunity_id = Column(Uuid(as_uuid=True), ForeignKey("job_opportunities.id", ondelete="CASCADE"), nullable=False)
    email_subject = Column(String, nullable=True)
    email_body = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    recommended_resume_id = Column(Uuid(as_uuid=True), nullable=True)
    selected_resume_id = Column(Uuid(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    recommended_certificate_ids = Column(JSON, nullable=False, default=list)
    ats_compatibility_score = Column(Integer, nullable=False, default=0)
    skill_match_score = Column(Integer, nullable=False, default=0)
    experience_match_score = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="Draft") # Draft, Ready
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    job_opportunity = relationship("JobOpportunity", back_populates="drafts")

class ApplicationRecord(Base):
    __tablename__ = "application_records"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    date_applied = Column(DateTime, default=datetime.utcnow, nullable=False)
    email_sent_body = Column(Text, nullable=False)
    email_subject = Column(String, nullable=False)
    sent_resume_url = Column(String, nullable=False)
    sent_certificate_urls = Column(JSON, nullable=False, default=list)
    status = Column(String, nullable=False, default="Sent") # Sent, Interview, Offered, Rejected, Failed
    thread_id = Column(String, nullable=True) # Gmail threadId for reply tracking

class FollowUpSchedule(Base):
    __tablename__ = "follow_up_schedules"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_record_id = Column(Uuid(as_uuid=True), ForeignKey("application_records.id", ondelete="CASCADE"), nullable=False)
    scheduled_days = Column(Integer, nullable=False) # 5, 10, 15
    scheduled_date = Column(DateTime, nullable=False)
    email_subject = Column(String, nullable=False)
    email_body = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="Pending") # Pending, Approved, Cancelled, Sent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, unique=True, index=True, nullable=False)
    tech_stack = Column(JSON, nullable=True)
    recent_products = Column(JSON, nullable=True)
    news_items = Column(JSON, nullable=True)
    last_refreshed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
