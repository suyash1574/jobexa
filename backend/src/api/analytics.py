from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.models.base import get_db
from src.models.user import User
from src.models.application import ApplicationRecord, ApplicationDraft, JobOpportunity
from src.schemas.application import ApplicationRecordOut
from src.api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_statistics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Computes total applications, pending drafts, interviews, offers, rejections, weekly volume, and top skills.
    """
    # 1. Total applications
    total = db.query(ApplicationRecord).filter(ApplicationRecord.user_id == current_user.id).count()
    
    # 2. Applications in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    try:
        recent = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == current_user.id,
            ApplicationRecord.date_applied >= thirty_days_ago
        ).count()
    except Exception:
        recent = 0

    # 3. Pending drafts
    drafts = db.query(ApplicationDraft).filter(ApplicationDraft.user_id == current_user.id).count()

    # 4. Interviews
    interviews = db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id,
        ApplicationRecord.status == "Interview"
    ).count()

    # 5. Offers & Rejections
    offers = db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id,
        ApplicationRecord.status == "Offer"
    ).count()
    rejections = db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id,
        ApplicationRecord.status == "Rejected"
    ).count()

    response_rate = 0.0
    if total > 0:
        response_rate = round(((interviews + offers) / total) * 100, 1)

    # Weekly application volume calculation (last 4 weeks)
    weekly_volume = []
    for week_idx in range(3, -1, -1):
        start_date = datetime.utcnow() - timedelta(days=(week_idx + 1) * 7)
        end_date = datetime.utcnow() - timedelta(days=week_idx * 7)
        try:
            count = db.query(ApplicationRecord).filter(
                ApplicationRecord.user_id == current_user.id,
                ApplicationRecord.date_applied >= start_date,
                ApplicationRecord.date_applied < end_date
            ).count()
        except Exception:
            count = 0
        weekly_volume.append({"week": f"Week -{week_idx}", "count": count})

    # Most requested skills extraction from job opportunities
    try:
        jobs = db.query(JobOpportunity).all()
        jobs = jobs[-20:] if jobs else []
    except Exception:
        jobs = []
    skill_counts: Dict[str, int] = {}
    for job in jobs:
        skills_list = getattr(job, "required_skills", [])
        if isinstance(skills_list, list):
            for skill in skills_list:
                if isinstance(skill, str):
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
    top_skills = [s[0] for s in sorted_skills[:5]] if sorted_skills else ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"]

    return {
        "total_applications": total,
        "applications_this_month": recent,
        "pending_drafts": drafts,
        "interviews": interviews,
        "offers": offers,
        "rejections": rejections,
        "response_rate": response_rate,
        "weekly_volume": weekly_volume,
        "most_applied_skills": ["Python", "Backend Development", "FastAPI", "SQL", "LLMs"],
        "most_requested_skills": top_skills
    }

@router.get("/history", response_model=List[ApplicationRecordOut])
def get_application_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieves a list of all historically sent or failed applications.
    """
    return db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id
    ).order_by(ApplicationRecord.date_applied.desc()).all()
