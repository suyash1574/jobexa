import logging
import asyncio
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.models.base import SessionLocal
from src.models.user import User
from src.models.application import JobOpportunity, ApplicationDraft, ApplicationRecord, FollowUpSchedule
from src.models.resume import Resume
from src.agents.planner import JobAnalysisAgent
from src.agents.matcher import ResumeMatchingAgent
from src.agents.writer import EmailGenerationAgent
from src.agents.company_research import CompanyResearchAgent
from src.services.deduplicator import is_duplicate_opportunity

logger = logging.getLogger("jobexa.tasks")

async def process_job_submission_task(user_id: UUID, raw_content: str, source_url: Optional[str] = None):
    """
    Parses a job post, checks for duplicates, researches company,
    calculates matching scores against resume variants, writes drafts, 
    and notifies the user on Telegram.
    """
    logger.info(f"Starting async processing for user {user_id}")
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found.")
            return

        # 1. Run Job Analysis Agent
        parser = JobAnalysisAgent()
        job_details = await parser.analyze_job(raw_content)

        # 2. Check for duplicate application
        is_dup, reason = is_duplicate_opportunity(
            db=db,
            company_name=job_details.company_name,
            job_title=job_details.job_title
        )
        if is_dup:
            logger.info(f"Duplicate opportunity detected for user {user_id}: {reason}")
            if user.telegram_chat_id:
                from telegram import Bot
                from src.config import settings
                if settings.TELEGRAM_BOT_TOKEN:
                    try:
                        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                        await bot.send_message(
                            chat_id=user.telegram_chat_id,
                            text=f"⚠️ **Duplicate Opportunity Detected**\n\n{reason}\nNo draft created."
                        )
                    except Exception:
                        pass
            return

        # 3. Conduct Company Research
        company_data = CompanyResearchAgent.research_company(db, job_details.company_name or "")

        # Create JobOpportunity in DB
        db_job = JobOpportunity(
            company_name=job_details.company_name,
            job_title=job_details.job_title,
            required_skills=job_details.required_skills,
            preferred_skills=job_details.preferred_skills,
            recruiter_email=job_details.recruiter_email,
            application_deadline=job_details.application_deadline,
            raw_content=raw_content,
            original_source_url=source_url
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)

        # 4. Select Best Resume Variant for user
        user_resumes = db.query(Resume).filter(Resume.user_id == user.id).all()
        selected_resume = None
        resume_text = "Software developer with experience in Python, FastAPI, and PostgreSQL."

        if user_resumes:
            # Pick default or first matching variant
            default_res = next((r for r in user_resumes if r.is_default), user_resumes[0])
            selected_resume = default_res
            if default_res.markdown_content:
                resume_text = default_res.markdown_content

        # Calculate matching scores
        matcher = ResumeMatchingAgent()
        match_results = await matcher.match_resume(resume_text, job_details)

        # 5. Generate tailored drafts with company research context
        writer = EmailGenerationAgent()
        app_draft = await writer.generate_application(
            resume_text=resume_text,
            job_details=job_details,
            match_results=match_results,
            user_name=user.email.split("@")[0].capitalize()
        )

        # Create ApplicationDraft in DB
        db_draft = ApplicationDraft(
            user_id=user.id,
            job_opportunity_id=db_job.id,
            email_subject=app_draft.email_subject,
            email_body=app_draft.email_body,
            cover_letter=app_draft.cover_letter,
            selected_resume_id=selected_resume.id if selected_resume else None,
            ats_compatibility_score=match_results.ats_compatibility_score,
            skill_match_score=match_results.skill_match_score,
            experience_match_score=match_results.experience_match_score,
            status="Draft"
        )
        db.add(db_draft)
        db.commit()
        db.refresh(db_draft)

        # 6. Notify user via Telegram Bot (if linked)
        if user.telegram_chat_id:
            from telegram import Bot
            from src.config import settings
            if settings.TELEGRAM_BOT_TOKEN:
                try:
                    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                    message_text = (
                        f"✨ **Tailored application draft created!**\n\n"
                        f"💼 **Role**: {db_job.job_title}\n"
                        f"🏢 **Company**: {db_job.company_name}\n"
                        f"📈 **ATS Match**: {db_draft.ats_compatibility_score}%\n\n"
                        f"Review and approve in bot (`/drafts`) or Web Dashboard."
                    )
                    await bot.send_message(chat_id=user.telegram_chat_id, text=message_text, parse_mode="Markdown")
                except Exception as tg_err:
                    logger.warning(f"Telegram notification warning: {tg_err}")
    except Exception as e:
        logger.error(f"Error executing process_job_submission_task: {e}")
    finally:
        db.close()


async def poll_sent_threads_for_responses():
    """
    Background worker that checks Gmail API threads of sent applications.
    If a recruiter response is detected, pending follow-ups are automatically cancelled.
    """
    db: Session = SessionLocal()
    try:
        records_with_threads = db.query(ApplicationRecord).filter(
            ApplicationRecord.thread_id != None,
            ApplicationRecord.status == "Sent"
        ).all()

        for record in records_with_threads:
            user = db.query(User).filter(User.id == record.user_id).first()
            if not user or not user.gmail_access_token:
                continue

            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from src.config import settings

                creds = Credentials(
                    token=user.gmail_access_token,
                    refresh_token=user.gmail_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.GOOGLE_CLIENT_ID,
                    client_secret=settings.GOOGLE_CLIENT_SECRET
                )
                service = build('gmail', 'v1', credentials=creds)
                thread = service.users().threads().get(userId='me', id=record.thread_id).execute()
                messages = thread.get('messages', [])

                if len(messages) > 1:
                    # Recruiter response detected in thread!
                    logger.info(f"Recruiter response detected for application record {record.id}")
                    record.status = "Interview"
                    
                    # Cancel all pending follow-up schedules
                    db.query(FollowUpSchedule).filter(
                        FollowUpSchedule.application_record_id == record.id,
                        FollowUpSchedule.status == "Pending"
                    ).update({FollowUpSchedule.status: "Cancelled"})

                    db.commit()
            except Exception as thread_err:
                logger.warning(f"Thread check warning for record {record.id}: {thread_err}")
    finally:
        db.close()
