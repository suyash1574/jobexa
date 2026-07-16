from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.models.base import get_db
from src.models.user import User
from src.models.application import ApplicationRecord, ApplicationDraft
from src.schemas.application import ApplicationRecordOut
from src.api.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard")
def get_dashboard_statistics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Computes application counts, drafts pending, and response rate.
    """
    total = db.query(ApplicationRecord).filter(ApplicationRecord.user_id == current_user.id).count()
    
    # Calculate apps in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent = db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id,
        ApplicationRecord.date_applied >= thirty_days_ago
    ).count()

    drafts = db.query(ApplicationDraft).filter(ApplicationDraft.user_id == current_user.id).count()
    
    # Simulate interview responses for analytics dashboard
    interviews = db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id,
        ApplicationRecord.status == "Interview"
    ).count()
    
    # Calculate response rate
    sent_count = db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id,
        ApplicationRecord.status == "Sent"
    ).count()
    
    rate = 0.0
    if total > 0:
        rate = round((sent_count / total) * 100, 1)

    return {
        "total_applications": total,
        "applications_this_month": recent,
        "pending_drafts": drafts,
        "interviews": interviews,
        "response_rate": rate
    }

@router.get("/history", response_model=List[ApplicationRecordOut])
def get_application_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieves a list of all historically sent or failed applications.
    """
    return db.query(ApplicationRecord).filter(
        ApplicationRecord.user_id == current_user.id
    ).order_by(ApplicationRecord.date_applied.desc()).all()
