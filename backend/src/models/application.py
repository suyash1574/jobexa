from sqlalchemy import Column, String, DateTime, Integer, Date, ForeignKey, Text
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
    recommended_resume_id = Column(UUID(as_uuid=True), nullable=True) # Will map to resumes table in Phase 5
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
    status = Column(String, nullable=False) # Sent, Interview, Offer, Rejected, Failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
