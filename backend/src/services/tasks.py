import logging
import asyncio
from uuid import UUID
from sqlalchemy.orm import Session
from typing import Optional

from src.models.base import SessionLocal
from src.models.user import User
from src.models.application import JobOpportunity, ApplicationDraft
from src.agents.planner import JobAnalysisAgent
from src.agents.matcher import ResumeMatchingAgent
from src.agents.writer import EmailGenerationAgent

# Simple Celery/Async Task runner simulation
logger = logging.getLogger("jobexa.tasks")

async def process_job_submission_task(user_id: UUID, raw_content: str, source_url: Optional[str] = None):
    """
    Parses a job post, calculates matching scores, writes drafts, 
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

        # 2. Retrieve default resume / profile
        # For Phase 3, if no resume exists yet, we use a fallback mock resume text
        resume_text = "Suyash's Resume: Software developer with 3 years of experience in Python, FastAPI, and PostgreSQL."
        
        # In later phases, we query the resumes table (Phase 5)
        # For now, we simulate matching
        matcher = ResumeMatchingAgent()
        match_results = await matcher.match_resume(resume_text, job_details)

        # 3. Generate tailored drafts
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
            ats_compatibility_score=match_results.ats_compatibility_score,
            skill_match_score=match_results.skill_match_score,
            experience_match_score=match_results.experience_match_score,
            status="Draft"
        )
        db.add(db_draft)
        db.commit()
        db.refresh(db_draft)

        # 4. Notify user via Telegram Bot (if linked)
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
                        f"🔗 **Review here**: http://localhost:8000/drafts/{db_draft.id}" # Local dashboard URL fallback
                    )
                    # Send message using standard HTTP POST call to Telegram API or bot client
                    # For simple compatibility, we can run bot.send_message
                    # Note: python-telegram-bot v20+ requires async client API
                    await bot.send_message(chat_id=user.telegram_chat_id, text=message_text, parse_mode="Markdown")
                except Exception as tg_err:
                    logger.error(f"Failed sending Telegram notification: {str(tg_err)}")
        
        logger.info(f"Completed processing for draft {db_draft.id}")
    except Exception as e:
        logger.error(f"Background task failed: {str(e)}")
    finally:
        db.close()
