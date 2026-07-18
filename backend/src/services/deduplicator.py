from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from src.models.application import JobOpportunity, ApplicationRecord

def is_duplicate_opportunity(
    db: Session,
    company_name: Optional[str],
    job_title: Optional[str],
    window_days: int = 30,
    similarity_threshold: float = 0.80
) -> Tuple[bool, Optional[str]]:
    """
    Checks if an application or opportunity already exists for a similar company name and job title
    within the specified window (default 30 days).
    Returns (is_duplicate: bool, reason: str).
    """
    if not company_name or not job_title:
        return False, None

    cutoff_date = datetime.utcnow() - timedelta(days=window_days)

    # 1. Check existing sent ApplicationRecords
    recent_records = db.query(ApplicationRecord).filter(
        ApplicationRecord.date_applied >= cutoff_date
    ).all()

    for record in recent_records:
        comp_sim = _calculate_similarity(company_name, record.company_name)
        title_sim = _calculate_similarity(job_title, record.position)

        if comp_sim >= similarity_threshold and title_sim >= similarity_threshold:
            return True, f"Already applied to {record.position} at {record.company_name} on {record.date_applied.strftime('%Y-%m-%d')}"

    # 2. Check existing JobOpportunities created recently
    recent_jobs = db.query(JobOpportunity).filter(
        JobOpportunity.created_at >= cutoff_date
    ).all()

    for job in recent_jobs:
        if not job.company_name or not job.job_title:
            continue
        comp_sim = _calculate_similarity(company_name, job.company_name)
        title_sim = _calculate_similarity(job_title, job.job_title)

        if comp_sim >= similarity_threshold and title_sim >= similarity_threshold:
            return True, f"Duplicate job posting for {job.job_title} at {job.company_name} submitted recently"

    return False, None

def _calculate_similarity(str1: str, str2: str) -> float:
    """Calculates Levenshtein/Sequence similarity ratio between two strings (0.0 to 1.0)."""
    if not str1 or not str2:
        return 0.0
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()
    return SequenceMatcher(None, s1, s2).ratio()
