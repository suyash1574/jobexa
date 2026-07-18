from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from src.models.base import Base

class JobOpportunity(Base):
    __tablename__ = "job_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    required_skills = Column(JSONB, nullable=False, default=list)
    preferred_skills = Column(JSONB, nullable=False, default=list)
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_opportunity_id = Column(UUID(as_uuid=True), ForeignKey("job_opportunities.id", ondelete="CASCADE"), nullable=False)
    email_subject = Column(String, nullable=True)
    email_body = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    recommended_resume_id = Column(UUID(as_uuid=True), nullable=True)
    selected_resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    recommended_certificate_ids = Column(JSONB, nullable=False, default=list)
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    date_applied = Column(DateTime, default=datetime.utcnow, nullable=False)
    email_sent_body = Column(Text, nullable=False)
    email_subject = Column(String, nullable=False)
    sent_resume_url = Column(String, nullable=False)
    sent_certificate_urls = Column(JSONB, nullable=False, default=list)
    thread_id = Column(String, nullable=True) # Gmail Thread ID
    status = Column(String, nullable=False) # Sent, Interview, Offer, Rejected, Failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    follow_ups = relationship("FollowUpSchedule", back_populates="application_record", cascade="all, delete-orphan")

class FollowUpSchedule(Base):
    __tablename__ = "follow_up_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_record_id = Column(UUID(as_uuid=True), ForeignKey("application_records.id", ondelete="CASCADE"), nullable=False)
    scheduled_days_after = Column(Integer, nullable=False, default=5)
    status = Column(String, nullable=False, default="Pending") # Pending, Approved, Sent, Cancelled
    email_subject = Column(String, nullable=False)
    email_body = Column(Text, nullable=False)
    scheduled_send_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application_record = relationship("ApplicationRecord", back_populates="follow_ups")

class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String, unique=True, index=True, nullable=False)
    tech_stack = Column(JSONB, nullable=False, default=list)
    recent_products = Column(JSONB, nullable=False, default=list)
    news_items = Column(JSONB, nullable=False, default=list)
    last_refreshed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
