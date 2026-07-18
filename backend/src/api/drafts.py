from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from datetime import datetime, timedelta

from src.models.base import get_db
from src.models.user import User
from src.models.application import ApplicationDraft, ApplicationRecord, JobOpportunity, FollowUpSchedule
from src.models.resume import Resume
from src.schemas.application import ApplicationDraftOut, ApplicationDraftUpdate
from src.api.auth import get_current_user
from src.services.gmail_sender import send_application_email_via_gmail
from src.services.pdf_compiler import compile_markdown_to_pdf

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

    # 1. Resolve Resume Attachment
    attachment_paths = []
    resume = None
    if draft.selected_resume_id:
        res_obj = db.query(Resume).filter(Resume.id == draft.selected_resume_id).first()
        if isinstance(res_obj, Resume):
            resume = res_obj
    if not resume:
        res_obj = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_default == True).first()
        if isinstance(res_obj, Resume):
            resume = res_obj

    sent_resume_url = getattr(resume, "file_url", "static/uploads/mock_default_resume.pdf") if resume else "static/uploads/mock_default_resume.pdf"
    
    if resume and getattr(resume, "markdown_content", None):
        try:
            compiled_pdf_path = compile_markdown_to_pdf(resume.markdown_content)
            attachment_paths.append(compiled_pdf_path)
        except Exception as e:
            if getattr(resume, "file_url", "").startswith("http"):
                attachment_paths.append(resume.file_url)

    try:
        # 2. Dispatch Email via Gmail API (or Fallback)
        dispatch_result = send_application_email_via_gmail(
            user=current_user,
            recipient_email=recruiter_email,
            subject=draft.email_subject or f"Application for {job.job_title} at {job.company_name}",
            body_text=draft.email_body or "",
            attachment_paths=attachment_paths
        )

        # 3. Create Application Record
        record = ApplicationRecord(
            user_id=current_user.id,
            company_name=job.company_name or "Unknown Company",
            position=job.job_title or "Unknown Position",
            email_sent_body=draft.email_body or "",
            email_subject=draft.email_subject or "",
            sent_resume_url=sent_resume_url,
            thread_id=dispatch_result.get("thread_id"),
            status=dispatch_result.get("status", "Sent")
        )
        db.add(record)
        db.flush()

        # 4. Schedule Automatic Follow-up Drafts (5, 10, and 15 days)
        for days in [5, 10, 15]:
            follow_up = FollowUpSchedule(
                application_record_id=record.id,
                scheduled_days_after=days,
                status="Pending",
                email_subject=f"Re: Application for {job.job_title} - Follow Up",
                email_body=f"Dear Hiring Team at {job.company_name},\n\nI wanted to follow up regarding my application for the {job.job_title} role submitted recently. Please let me know if you need any additional information.\n\nBest regards,",
                scheduled_send_at=datetime.utcnow() + timedelta(days=days)
            )
            db.add(follow_up)
        
        # Delete draft on success
        db.delete(draft)
        db.commit()
        return {"message": "Application sent successfully", "application_record_id": record.id, "thread_id": dispatch_result.get("thread_id")}

    except Exception as e:
        db.rollback()
        # On failure, create a failed ApplicationRecord
        record = ApplicationRecord(
            user_id=current_user.id,
            company_name=job.company_name or "Unknown Company",
            position=job.job_title or "Unknown Position",
            email_sent_body=draft.email_body or "",
            email_subject=draft.email_subject or "",
            sent_resume_url=sent_resume_url,
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
                except Exception:
                    pass

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Email dispatch failed: {str(e)}"
        )
