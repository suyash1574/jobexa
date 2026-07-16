from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from src.models.base import get_db
from src.models.user import User
from src.models.application import ApplicationDraft, ApplicationRecord, JobOpportunity
from src.schemas.application import ApplicationDraftOut, ApplicationDraftUpdate
from src.api.auth import get_current_user
from src.services.email import EmailService

router = APIRouter(prefix="/drafts", tags=["Drafts"])

@router.get("", response_model=List[ApplicationDraftOut])
def list_drafts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    drafts = db.query(ApplicationDraft).filter(ApplicationDraft.user_id == current_user.id).all()
    return drafts

@router.get("/{id}", response_model=ApplicationDraftOut)
def get_draft(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft = db.query(ApplicationDraft).filter(
        ApplicationDraft.id == id,
        ApplicationDraft.user_id == current_user.id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@router.put("/{id}", response_model=ApplicationDraftOut)
def update_draft(
    id: UUID, 
    draft_in: ApplicationDraftUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    draft = db.query(ApplicationDraft).filter(
        ApplicationDraft.id == id,
        ApplicationDraft.user_id == current_user.id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    update_data = draft_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)

    db.commit()
    db.refresh(draft)
    return draft

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draft(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft = db.query(ApplicationDraft).filter(
        ApplicationDraft.id == id,
        ApplicationDraft.user_id == current_user.id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    db.delete(draft)
    db.commit()
    return

@router.post("/{id}/approve")
async def approve_and_send_draft(
    id: UUID, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    draft = db.query(ApplicationDraft).filter(
        ApplicationDraft.id == id,
        ApplicationDraft.user_id == current_user.id
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    job = draft.job_opportunity
    recruiter_email = job.recruiter_email

    if not recruiter_email:
        raise HTTPException(
            status_code=400, 
            detail="Cannot approve application: recruiter email is missing. Please edit the opportunity details."
        )

    # For Phase 4, we assume mock resume PDF file if none uploaded
    attachment_paths = []
    
    try:
        # Trigger email dispatch
        EmailService.send_application_email(
            to_email=recruiter_email,
            subject=draft.email_subject or f"Application for {job.job_title}",
            body=draft.email_body or "",
            attachment_paths=attachment_paths
        )

        # Create historical ApplicationRecord
        record = ApplicationRecord(
            user_id=current_user.id,
            company_name=job.company_name or "Unknown Company",
            position=job.job_title or "Unknown Position",
            email_sent_body=draft.email_body or "",
            email_subject=draft.email_subject or "",
            sent_resume_url="https://supabase-storage/resumes/mock_default.pdf",
            status="Sent"
        )
        db.add(record)
        
        # Delete draft on success
        db.delete(draft)
        db.commit()
        return {"message": "Application sent successfully", "application_record_id": record.id}

    except Exception as e:
        # On failure, create a failed ApplicationRecord
        record = ApplicationRecord(
            user_id=current_user.id,
            company_name=job.company_name or "Unknown Company",
            position=job.job_title or "Unknown Position",
            email_sent_body=draft.email_body or "",
            email_subject=draft.email_subject or "",
            sent_resume_url="https://supabase-storage/resumes/mock_default.pdf",
            status="Failed"
        )
        db.add(record)
        db.commit()

        # Send Telegram alert to user (if linked)
        if current_user.telegram_chat_id:
            from telegram import Bot
            from src.config import settings
            if settings.TELEGRAM_BOT_TOKEN:
                try:
                    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                    alert_text = (
                        f"🚨 **Failed to send application!**\n\n"
                        f"💼 **Role**: {job.job_title}\n"
                        f"🏢 **Company**: {job.company_name}\n"
                        f"⚠️ **Reason**: {str(e)}"
                    )
                    await bot.send_message(chat_id=current_user.telegram_chat_id, text=alert_text, parse_mode="Markdown")
                except Exception as tg_err:
                    pass

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Email dispatch failed: {str(e)}"
        )
