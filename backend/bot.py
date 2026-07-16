import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from datetime import datetime
import asyncio
import uuid

# Setup sys.path to backend directory
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import settings
from src.models.base import SessionLocal
from src.models.user import User
from src.models.resume import Resume, Certificate
from src.models.application import JobOpportunity, ApplicationDraft, ApplicationRecord
from src.services.tasks import process_job_submission_task

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("jobexa.bot")


# ─── Helper: get linked user from chat_id ───────────────────────────────────
def get_user_by_chat(chat_id: str):
    """Returns (user, db_session) or (None, db_session) if not linked."""
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
    return user, db


def require_linked(func):
    """Decorator that checks if the user's Telegram is linked before executing."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_chat.id)
        user, db = get_user_by_chat(chat_id)
        db.close()
        if not user:
            await update.message.reply_text(
                "⚠️ Your account is not linked.\n\n"
                "1️⃣ Go to your Jobexa web dashboard\n"
                "2️⃣ Click **Link Telegram**\n"
                "3️⃣ Use `/link <code>` here with the pairing code",
                parse_mode="Markdown"
            )
            return
        return await func(update, context, user)
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("📊 Dashboard Status", callback_data="cmd_status"),
         InlineKeyboardButton("📝 My Drafts", callback_data="cmd_drafts")],
        [InlineKeyboardButton("📄 My Resumes", callback_data="cmd_resumes"),
         InlineKeyboardButton("🏅 Certificates", callback_data="cmd_certificates")],
        [InlineKeyboardButton("📜 Application History", callback_data="cmd_history"),
         InlineKeyboardButton("❓ Help", callback_data="cmd_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 *Welcome to Jobexa!*\n"
        "Your AI-powered career assistant.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *Quick Start:*\n"
        "• Send a job posting (text, PDF, or screenshot)\n"
        "• I'll analyze it and create a tailored application draft\n"
        "• Review, approve, and send — all from here!\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Use the buttons below or type `/help` for all commands.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *Jobexa Command Reference*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 *Account*\n"
        "  `/link <code>` — Pair your Telegram account\n"
        "  `/unlink` — Unpair your account\n\n"
        "📊 *Dashboard*\n"
        "  `/status` — View your stats & metrics\n"
        "  `/drafts` — List pending application drafts\n"
        "  `/history` — View sent application history\n\n"
        "📁 *Documents*\n"
        "  `/resumes` — List your uploaded resumes\n"
        "  `/certificates` — List your certificates\n\n"
        "💼 *Job Submissions*\n"
        "  📝 Send text → paste a job description\n"
        "  📎 Send PDF → upload as resume OR job posting\n"
        "  📸 Send photo → OCR a job screenshot\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tip:* After I create a draft, use the\n"
        "✅ Approve or ❌ Reject buttons to take action!"
    )
    await (update.message or update.callback_query.message).reply_text(text, parse_mode="Markdown")


# ─── /link ──────────────────────────────────────────────────────────────────
async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Please specify the pairing code.\nExample: `/link 123456`", parse_mode="Markdown")
        return

    code = context.args[0]
    chat_id = str(update.effective_chat.id)

    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.telegram_pairing_token == code,
            User.pairing_token_expires_at > datetime.utcnow()
        ).first()

        if user:
            user.telegram_chat_id = chat_id
            user.telegram_pairing_token = None
            user.pairing_token_expires_at = None
            db.commit()
            await update.message.reply_text(
                "✅ *Accounts paired successfully!*\n\n"
                "You can now:\n"
                "• Send job postings directly here\n"
                "• Review and approve drafts\n"
                "• Check your application status\n\n"
                "Type `/help` to see all commands.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Invalid or expired pairing code. Please generate a new one on the dashboard.")
    except Exception as e:
        logger.error(f"Error pairing Telegram account: {str(e)}")
        await update.message.reply_text("❌ An error occurred while pairing. Please try again.")
    finally:
        db.close()


# ─── /unlink ────────────────────────────────────────────────────────────────
async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user:
            user.telegram_chat_id = None
            db.commit()
            await update.message.reply_text("✅ Account unlinked. Use `/link <code>` to pair again.", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ No account is linked to this Telegram chat.")
    except Exception as e:
        logger.error(f"Error unlinking account: {str(e)}")
        await update.message.reply_text("❌ Failed to unlink. Please try again.")
    finally:
        db.close()


# ─── /status ────────────────────────────────────────────────────────────────
@require_linked
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    db = SessionLocal()
    try:
        total_apps = db.query(ApplicationRecord).filter(ApplicationRecord.user_id == user.id).count()
        pending_drafts = db.query(ApplicationDraft).filter(ApplicationDraft.user_id == user.id).count()
        sent_apps = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == user.id,
            ApplicationRecord.status == "Sent"
        ).count()
        failed_apps = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == user.id,
            ApplicationRecord.status == "Failed"
        ).count()
        resumes_count = db.query(Resume).filter(Resume.user_id == user.id).count()

        # Calculate response rate
        response_rate = 0
        if total_apps > 0:
            non_sent = db.query(ApplicationRecord).filter(
                ApplicationRecord.user_id == user.id,
                ApplicationRecord.status.notin_(["Sent", "Failed"])
            ).count()
            response_rate = round((non_sent / total_apps) * 100)

        text = (
            "📊 *Your Jobexa Dashboard*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📨 Total Applications: *{total_apps}*\n"
            f"✅ Sent: *{sent_apps}*\n"
            f"❌ Failed: *{failed_apps}*\n"
            f"📝 Pending Drafts: *{pending_drafts}*\n"
            f"📄 Resumes Uploaded: *{resumes_count}*\n"
            f"📈 Response Rate: *{response_rate}%*\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )

        keyboard = [
            [InlineKeyboardButton("📝 View Drafts", callback_data="cmd_drafts"),
             InlineKeyboardButton("📜 View History", callback_data="cmd_history")]
        ]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()


# ─── /drafts ────────────────────────────────────────────────────────────────
@require_linked
async def drafts_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    db = SessionLocal()
    try:
        drafts = db.query(ApplicationDraft).filter(
            ApplicationDraft.user_id == user.id
        ).order_by(ApplicationDraft.created_at.desc()).limit(10).all()

        if not drafts:
            await update.message.reply_text(
                "📝 *No pending drafts.*\n\n"
                "Send me a job posting (text, PDF, or screenshot)\nto create your first draft!",
                parse_mode="Markdown"
            )
            return

        await update.message.reply_text(
            f"📝 *Pending Drafts ({len(drafts)})*\n━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )

        for draft in drafts:
            job = db.query(JobOpportunity).filter(JobOpportunity.id == draft.job_opportunity_id).first()
            company = job.company_name if job else "Unknown"
            role = job.job_title if job else "Unknown Role"
            ats = draft.ats_compatibility_score or 0

            # ATS score emoji
            ats_emoji = "🟢" if ats >= 75 else ("🟡" if ats >= 50 else "🔴")

            text = (
                f"💼 *{role}*\n"
                f"🏢 {company}\n"
                f"{ats_emoji} ATS Match: *{ats}%*\n"
                f"📅 {draft.created_at.strftime('%b %d, %Y') if draft.created_at else 'N/A'}"
            )

            keyboard = [[
                InlineKeyboardButton("👁 View", callback_data=f"view_{draft.id}"),
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{draft.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft.id}")
            ]]

            await update.message.reply_text(
                text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    finally:
        db.close()


# ─── /history ───────────────────────────────────────────────────────────────
@require_linked
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    db = SessionLocal()
    try:
        records = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == user.id
        ).order_by(ApplicationRecord.date_applied.desc()).limit(10).all()

        if not records:
            await update.message.reply_text(
                "📜 *No applications sent yet.*\n\n"
                "Submit a job posting and approve the draft to get started!",
                parse_mode="Markdown"
            )
            return

        lines = ["📜 *Application History (Last 10)*\n━━━━━━━━━━━━━━━━━━━━━\n"]
        status_emoji = {
            "Sent": "📨", "Interview": "🎯", "Offer": "🎉",
            "Rejected": "😔", "Failed": "❌"
        }

        for r in records:
            emoji = status_emoji.get(r.status, "📋")
            date_str = r.date_applied.strftime('%b %d') if r.date_applied else "N/A"
            lines.append(
                f"{emoji} *{r.position}* @ {r.company_name}\n"
                f"    Status: {r.status} | {date_str}"
            )

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


# ─── /resumes ───────────────────────────────────────────────────────────────
@require_linked
async def resumes_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    db = SessionLocal()
    try:
        resumes = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.created_at.desc()).all()

        if not resumes:
            await update.message.reply_text(
                "📄 *No resumes uploaded.*\n\n"
                "Send me a PDF file and I'll ask if you want\nto upload it as a resume!",
                parse_mode="Markdown"
            )
            return

        lines = [f"📄 *Your Resumes ({len(resumes)})*\n━━━━━━━━━━━━━━━━━━━━━\n"]
        for i, r in enumerate(resumes, 1):
            default_badge = " ⭐ Default" if r.is_default else ""
            tag = f" [{r.role_tag}]" if r.role_tag else ""
            size_kb = round(r.file_size / 1024, 1) if r.file_size else "?"
            lines.append(
                f"*{i}.* {r.filename}{tag}{default_badge}\n"
                f"    📏 {size_kb} KB | {r.created_at.strftime('%b %d, %Y') if r.created_at else 'N/A'}"
            )

        keyboard = [[InlineKeyboardButton("📤 Upload via Web Dashboard", url="https://jobexa.vercel.app")]]
        await update.message.reply_text(
            "\n\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()


# ─── /certificates ──────────────────────────────────────────────────────────
@require_linked
async def certificates_command(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User) -> None:
    db = SessionLocal()
    try:
        certs = db.query(Certificate).filter(Certificate.user_id == user.id).order_by(Certificate.created_at.desc()).all()

        if not certs:
            await update.message.reply_text(
                "🏅 *No certificates uploaded.*\n\n"
                "Upload certificates on the web dashboard to\nstrengthen your applications!",
                parse_mode="Markdown"
            )
            return

        lines = [f"🏅 *Your Certificates ({len(certs)})*\n━━━━━━━━━━━━━━━━━━━━━\n"]
        for i, c in enumerate(certs, 1):
            cat = f" [{c.category}]" if c.category else ""
            lines.append(
                f"*{i}.* {c.filename}{cat}\n"
                f"    {c.created_at.strftime('%b %d, %Y') if c.created_at else 'N/A'}"
            )

        keyboard = [[InlineKeyboardButton("📤 Upload via Web Dashboard", url="https://jobexa.vercel.app")]]
        await update.message.reply_text(
            "\n\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════
# CALLBACK QUERY HANDLER (Inline Keyboard Buttons)
# ═══════════════════════════════════════════════════════════════════════════

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = str(query.message.chat.id)

    # ─── Navigation commands from /start buttons ───
    if data == "cmd_status":
        user, db = get_user_by_chat(chat_id)
        db.close()
        if not user:
            await query.message.reply_text("⚠️ Account not linked. Use `/link <code>` first.", parse_mode="Markdown")
            return
        # Simulate /status by directly calling the inner logic
        await _send_status(query.message, user)
        return

    if data == "cmd_drafts":
        user, db = get_user_by_chat(chat_id)
        db.close()
        if not user:
            await query.message.reply_text("⚠️ Account not linked. Use `/link <code>` first.", parse_mode="Markdown")
            return
        await _send_drafts(query.message, user)
        return

    if data == "cmd_history":
        user, db = get_user_by_chat(chat_id)
        db.close()
        if not user:
            await query.message.reply_text("⚠️ Account not linked. Use `/link <code>` first.", parse_mode="Markdown")
            return
        await _send_history(query.message, user)
        return

    if data == "cmd_resumes":
        user, db = get_user_by_chat(chat_id)
        db.close()
        if not user:
            await query.message.reply_text("⚠️ Account not linked. Use `/link <code>` first.", parse_mode="Markdown")
            return
        await _send_resumes(query.message, user)
        return

    if data == "cmd_certificates":
        user, db = get_user_by_chat(chat_id)
        db.close()
        if not user:
            await query.message.reply_text("⚠️ Account not linked. Use `/link <code>` first.", parse_mode="Markdown")
            return
        await _send_certificates(query.message, user)
        return

    if data == "cmd_help":
        await _send_help(query.message)
        return

    # ─── View Draft ───
    if data.startswith("view_"):
        draft_id = data.replace("view_", "")
        await _view_draft(query.message, chat_id, draft_id)
        return

    # ─── Approve Draft (show confirmation) ───
    if data.startswith("approve_"):
        draft_id = data.replace("approve_", "")
        await _confirm_approve(query.message, chat_id, draft_id)
        return

    # ─── Confirm Approve (actually send) ───
    if data.startswith("confirm_approve_"):
        draft_id = data.replace("confirm_approve_", "")
        await _execute_approve(query.message, chat_id, draft_id)
        return

    # ─── Cancel Approve ───
    if data == "cancel_approve":
        await query.message.reply_text("↩️ Approval cancelled.")
        return

    # ─── Reject Draft ───
    if data.startswith("reject_"):
        draft_id = data.replace("reject_", "")
        await _execute_reject(query.message, chat_id, draft_id)
        return

    # ─── PDF Upload as Resume ───
    if data.startswith("upload_resume_"):
        file_id = data.replace("upload_resume_", "")
        await _upload_as_resume(query.message, chat_id, file_id, context)
        return

    # ─── PDF Submit as Job ───
    if data.startswith("submit_job_"):
        file_id = data.replace("submit_job_", "")
        await _submit_as_job(query.message, chat_id, file_id, context)
        return


# ═══════════════════════════════════════════════════════════════════════════
# REUSABLE INNER FUNCTIONS (called from both commands & callbacks)
# ═══════════════════════════════════════════════════════════════════════════

async def _send_help(message):
    text = (
        "📖 *Jobexa Command Reference*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔗 *Account*\n"
        "  `/link <code>` — Pair your Telegram account\n"
        "  `/unlink` — Unpair your account\n\n"
        "📊 *Dashboard*\n"
        "  `/status` — View your stats & metrics\n"
        "  `/drafts` — List pending application drafts\n"
        "  `/history` — View sent application history\n\n"
        "📁 *Documents*\n"
        "  `/resumes` — List your uploaded resumes\n"
        "  `/certificates` — List your certificates\n\n"
        "💼 *Job Submissions*\n"
        "  📝 Send text → paste a job description\n"
        "  📎 Send PDF → upload as resume OR job posting\n"
        "  📸 Send photo → OCR a job screenshot\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tip:* After I create a draft, use the\n"
        "✅ Approve or ❌ Reject buttons to take action!"
    )
    await message.reply_text(text, parse_mode="Markdown")


async def _send_status(message, user):
    db = SessionLocal()
    try:
        total_apps = db.query(ApplicationRecord).filter(ApplicationRecord.user_id == user.id).count()
        pending_drafts = db.query(ApplicationDraft).filter(ApplicationDraft.user_id == user.id).count()
        sent_apps = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == user.id, ApplicationRecord.status == "Sent"
        ).count()
        failed_apps = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == user.id, ApplicationRecord.status == "Failed"
        ).count()
        resumes_count = db.query(Resume).filter(Resume.user_id == user.id).count()

        response_rate = 0
        if total_apps > 0:
            non_sent = db.query(ApplicationRecord).filter(
                ApplicationRecord.user_id == user.id,
                ApplicationRecord.status.notin_(["Sent", "Failed"])
            ).count()
            response_rate = round((non_sent / total_apps) * 100)

        text = (
            "📊 *Your Jobexa Dashboard*\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📨 Total Applications: *{total_apps}*\n"
            f"✅ Sent: *{sent_apps}*\n"
            f"❌ Failed: *{failed_apps}*\n"
            f"📝 Pending Drafts: *{pending_drafts}*\n"
            f"📄 Resumes Uploaded: *{resumes_count}*\n"
            f"📈 Response Rate: *{response_rate}%*\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [
            [InlineKeyboardButton("📝 View Drafts", callback_data="cmd_drafts"),
             InlineKeyboardButton("📜 View History", callback_data="cmd_history")]
        ]
        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()


async def _send_drafts(message, user):
    db = SessionLocal()
    try:
        drafts = db.query(ApplicationDraft).filter(
            ApplicationDraft.user_id == user.id
        ).order_by(ApplicationDraft.created_at.desc()).limit(10).all()

        if not drafts:
            await message.reply_text(
                "📝 *No pending drafts.*\n\nSend me a job posting to create your first draft!",
                parse_mode="Markdown"
            )
            return

        await message.reply_text(
            f"📝 *Pending Drafts ({len(drafts)})*\n━━━━━━━━━━━━━━━━━━━━━",
            parse_mode="Markdown"
        )

        for draft in drafts:
            job = db.query(JobOpportunity).filter(JobOpportunity.id == draft.job_opportunity_id).first()
            company = job.company_name if job else "Unknown"
            role = job.job_title if job else "Unknown Role"
            ats = draft.ats_compatibility_score or 0
            ats_emoji = "🟢" if ats >= 75 else ("🟡" if ats >= 50 else "🔴")

            text = (
                f"💼 *{role}*\n"
                f"🏢 {company}\n"
                f"{ats_emoji} ATS Match: *{ats}%*\n"
                f"📅 {draft.created_at.strftime('%b %d, %Y') if draft.created_at else 'N/A'}"
            )
            keyboard = [[
                InlineKeyboardButton("👁 View", callback_data=f"view_{draft.id}"),
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{draft.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft.id}")
            ]]
            await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()


async def _send_history(message, user):
    db = SessionLocal()
    try:
        records = db.query(ApplicationRecord).filter(
            ApplicationRecord.user_id == user.id
        ).order_by(ApplicationRecord.date_applied.desc()).limit(10).all()

        if not records:
            await message.reply_text(
                "📜 *No applications sent yet.*\n\nSubmit a job posting and approve a draft to get started!",
                parse_mode="Markdown"
            )
            return

        lines = ["📜 *Application History (Last 10)*\n━━━━━━━━━━━━━━━━━━━━━\n"]
        status_emoji = {"Sent": "📨", "Interview": "🎯", "Offer": "🎉", "Rejected": "😔", "Failed": "❌"}
        for r in records:
            emoji = status_emoji.get(r.status, "📋")
            date_str = r.date_applied.strftime('%b %d') if r.date_applied else "N/A"
            lines.append(f"{emoji} *{r.position}* @ {r.company_name}\n    Status: {r.status} | {date_str}")

        await message.reply_text("\n\n".join(lines), parse_mode="Markdown")
    finally:
        db.close()


async def _send_resumes(message, user):
    db = SessionLocal()
    try:
        resumes = db.query(Resume).filter(Resume.user_id == user.id).order_by(Resume.created_at.desc()).all()
        if not resumes:
            await message.reply_text(
                "📄 *No resumes uploaded.*\n\nSend me a PDF to upload it as a resume!",
                parse_mode="Markdown"
            )
            return

        lines = [f"📄 *Your Resumes ({len(resumes)})*\n━━━━━━━━━━━━━━━━━━━━━\n"]
        for i, r in enumerate(resumes, 1):
            default_badge = " ⭐ Default" if r.is_default else ""
            tag = f" [{r.role_tag}]" if r.role_tag else ""
            size_kb = round(r.file_size / 1024, 1) if r.file_size else "?"
            lines.append(f"*{i}.* {r.filename}{tag}{default_badge}\n    📏 {size_kb} KB")

        keyboard = [[InlineKeyboardButton("📤 Upload via Dashboard", url="https://jobexa.vercel.app")]]
        await message.reply_text("\n\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()


async def _send_certificates(message, user):
    db = SessionLocal()
    try:
        certs = db.query(Certificate).filter(Certificate.user_id == user.id).order_by(Certificate.created_at.desc()).all()
        if not certs:
            await message.reply_text(
                "🏅 *No certificates uploaded.*\n\nUpload certificates on the web dashboard!",
                parse_mode="Markdown"
            )
            return

        lines = [f"🏅 *Your Certificates ({len(certs)})*\n━━━━━━━━━━━━━━━━━━━━━\n"]
        for i, c in enumerate(certs, 1):
            cat = f" [{c.category}]" if c.category else ""
            lines.append(f"*{i}.* {c.filename}{cat}")

        keyboard = [[InlineKeyboardButton("📤 Upload via Dashboard", url="https://jobexa.vercel.app")]]
        await message.reply_text("\n\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()


# ─── Draft Actions ──────────────────────────────────────────────────────────

async def _view_draft(message, chat_id, draft_id):
    user, db = get_user_by_chat(chat_id)
    try:
        if not user:
            await message.reply_text("⚠️ Account not linked.")
            return

        draft = db.query(ApplicationDraft).filter(
            ApplicationDraft.id == draft_id,
            ApplicationDraft.user_id == user.id
        ).first()

        if not draft:
            await message.reply_text("❌ Draft not found or already processed.")
            return

        job = db.query(JobOpportunity).filter(JobOpportunity.id == draft.job_opportunity_id).first()
        company = job.company_name if job else "Unknown"
        role = job.job_title if job else "Unknown Role"
        recruiter = job.recruiter_email if job else "Not found"
        skills = ", ".join(job.required_skills[:5]) if job and job.required_skills else "N/A"

        # Truncate email body for Telegram (max ~3000 chars)
        body_preview = (draft.email_body or "No body generated.")[:1500]
        if len(draft.email_body or "") > 1500:
            body_preview += "\n\n_...truncated. View full draft on web dashboard._"

        text = (
            f"📋 *Draft Details*\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💼 *Role:* {role}\n"
            f"🏢 *Company:* {company}\n"
            f"📧 *Recruiter:* {recruiter}\n"
            f"🔧 *Key Skills:* {skills}\n\n"
            f"📈 *Scores:*\n"
            f"  ATS: {draft.ats_compatibility_score or 0}%"
            f" | Skills: {draft.skill_match_score or 0}%"
            f" | Experience: {draft.experience_match_score or 0}%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✉️ *Subject:* {draft.email_subject or 'N/A'}\n\n"
            f"📝 *Email Body:*\n{body_preview}"
        )

        keyboard = [[
            InlineKeyboardButton("✅ Approve & Send", callback_data=f"approve_{draft.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{draft.id}")
        ], [
            InlineKeyboardButton("✏️ Edit on Dashboard", url="https://jobexa.vercel.app")
        ]]

        await message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        db.close()


async def _confirm_approve(message, chat_id, draft_id):
    user, db = get_user_by_chat(chat_id)
    try:
        if not user:
            await message.reply_text("⚠️ Account not linked.")
            return

        draft = db.query(ApplicationDraft).filter(
            ApplicationDraft.id == draft_id,
            ApplicationDraft.user_id == user.id
        ).first()

        if not draft:
            await message.reply_text("❌ Draft not found or already processed.")
            return

        job = db.query(JobOpportunity).filter(JobOpportunity.id == draft.job_opportunity_id).first()
        company = job.company_name if job else "Unknown"
        role = job.job_title if job else "Unknown Role"
        recruiter = job.recruiter_email if job else "Not set"

        keyboard = [[
            InlineKeyboardButton("✅ Yes, Send It!", callback_data=f"confirm_approve_{draft_id}"),
            InlineKeyboardButton("↩️ Cancel", callback_data="cancel_approve")
        ]]

        await message.reply_text(
            f"⚠️ *Confirm Application Send*\n\n"
            f"💼 *{role}* @ {company}\n"
            f"📧 To: {recruiter}\n\n"
            f"This will send the application email to the recruiter.\n"
            f"Are you sure?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()


async def _execute_approve(message, chat_id, draft_id):
    user, db = get_user_by_chat(chat_id)
    try:
        if not user:
            await message.reply_text("⚠️ Account not linked.")
            return

        draft = db.query(ApplicationDraft).filter(
            ApplicationDraft.id == draft_id,
            ApplicationDraft.user_id == user.id
        ).first()

        if not draft:
            await message.reply_text("❌ Draft not found or already processed.")
            return

        job = db.query(JobOpportunity).filter(JobOpportunity.id == draft.job_opportunity_id).first()

        if not job or not job.recruiter_email:
            await message.reply_text(
                "❌ *Cannot send:* Recruiter email is missing.\n"
                "Edit the draft on the web dashboard to add it.",
                parse_mode="Markdown"
            )
            return

        await message.reply_text("📤 Sending application email...")

        try:
            from src.services.email import EmailService
            EmailService.send_application_email(
                to_email=job.recruiter_email,
                subject=draft.email_subject or f"Application for {job.job_title}",
                body=draft.email_body or "",
                attachment_paths=[]
            )

            # Create success record
            record = ApplicationRecord(
                user_id=user.id,
                company_name=job.company_name or "Unknown Company",
                position=job.job_title or "Unknown Position",
                email_sent_body=draft.email_body or "",
                email_subject=draft.email_subject or "",
                sent_resume_url="",
                status="Sent"
            )
            db.add(record)
            db.delete(draft)
            db.commit()

            await message.reply_text(
                f"✅ *Application sent successfully!*\n\n"
                f"💼 {job.job_title} @ {job.company_name}\n"
                f"📧 Sent to: {job.recruiter_email}\n\n"
                f"Track it in `/history`.",
                parse_mode="Markdown"
            )

        except Exception as e:
            # Create failed record
            record = ApplicationRecord(
                user_id=user.id,
                company_name=job.company_name or "Unknown Company",
                position=job.job_title or "Unknown Position",
                email_sent_body=draft.email_body or "",
                email_subject=draft.email_subject or "",
                sent_resume_url="",
                status="Failed"
            )
            db.add(record)
            db.commit()

            await message.reply_text(
                f"🚨 *Failed to send application!*\n\n"
                f"💼 {job.job_title} @ {job.company_name}\n"
                f"⚠️ Reason: {str(e)[:200]}\n\n"
                f"The draft is still available. Try again or edit on the dashboard.",
                parse_mode="Markdown"
            )
    finally:
        db.close()


async def _execute_reject(message, chat_id, draft_id):
    user, db = get_user_by_chat(chat_id)
    try:
        if not user:
            await message.reply_text("⚠️ Account not linked.")
            return

        draft = db.query(ApplicationDraft).filter(
            ApplicationDraft.id == draft_id,
            ApplicationDraft.user_id == user.id
        ).first()

        if not draft:
            await message.reply_text("❌ Draft not found or already processed.")
            return

        job = db.query(JobOpportunity).filter(JobOpportunity.id == draft.job_opportunity_id).first()
        role = job.job_title if job else "Unknown"
        company = job.company_name if job else "Unknown"

        db.delete(draft)
        db.commit()

        await message.reply_text(
            f"🗑 *Draft rejected and deleted.*\n\n"
            f"💼 {role} @ {company}",
            parse_mode="Markdown"
        )
    finally:
        db.close()


# ─── PDF Upload as Resume ───────────────────────────────────────────────────

async def _upload_as_resume(message, chat_id, file_id, context):
    user, db = get_user_by_chat(chat_id)
    try:
        if not user:
            await message.reply_text("⚠️ Account not linked.")
            return

        await message.reply_text("📤 Uploading your resume...")

        file = await context.bot.get_file(file_id)
        pdf_bytes = await file.download_as_bytearray()

        from src.services.storage import StorageService
        filename = f"telegram_resume_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_url = StorageService.upload_file(
            file_bytes=bytes(pdf_bytes),
            filename=filename,
            folder="resumes"
        )

        # Check if this is the user's first resume (make it default)
        existing = db.query(Resume).filter(Resume.user_id == user.id).count()

        new_resume = Resume(
            id=uuid.uuid4(),
            user_id=user.id,
            filename=filename,
            file_url=file_url,
            file_size=len(pdf_bytes),
            role_tag=None,
            is_default=(existing == 0)
        )
        db.add(new_resume)
        db.commit()

        default_text = " (set as default ⭐)" if existing == 0 else ""
        await message.reply_text(
            f"✅ *Resume uploaded!*{default_text}\n\n"
            f"📄 {filename}\n"
            f"📏 {round(len(pdf_bytes) / 1024, 1)} KB\n\n"
            f"Use `/resumes` to see all your resumes.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Resume upload failed: {str(e)}")
        await message.reply_text(f"❌ Upload failed: {str(e)[:200]}")
    finally:
        db.close()


async def _submit_as_job(message, chat_id, file_id, context):
    user, db = get_user_by_chat(chat_id)
    db.close()
    if not user:
        await message.reply_text("⚠️ Account not linked.")
        return

    await message.reply_text("📥 Downloading PDF job description...")

    file = await context.bot.get_file(file_id)
    pdf_bytes = await file.download_as_bytearray()

    from src.services.parser import DocumentParserService
    content = DocumentParserService.parse_pdf(bytes(pdf_bytes))

    if not content or len(content.strip()) < 10:
        await message.reply_text("❌ Could not extract enough text from the PDF.")
        return

    await message.reply_text("🔍 Processing job description... This might take a moment.")
    asyncio.create_task(
        process_job_submission_task(user_id=user.id, raw_content=content)
    )


# ═══════════════════════════════════════════════════════════════════════════
# MESSAGE HANDLERS (Text, PDF, Photo)
# ═══════════════════════════════════════════════════════════════════════════

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    user, db = get_user_by_chat(chat_id)
    db.close()

    if not user:
        await update.message.reply_text(
            "⚠️ Your account is not linked. Use `/link <code>` first.",
            parse_mode="Markdown"
        )
        return

    content = update.message.text
    if not content or len(content.strip()) < 10:
        await update.message.reply_text("❌ Message too short. Please paste the full job description.")
        return

    await update.message.reply_text("🔍 Processing job description... This might take a moment.")
    asyncio.create_task(
        process_job_submission_task(user_id=user.id, raw_content=content)
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    user, db = get_user_by_chat(chat_id)
    db.close()

    if not user:
        await update.message.reply_text(
            "⚠️ Your account is not linked. Use `/link <code>` first.",
            parse_mode="Markdown"
        )
        return

    doc = update.message.document
    if doc.mime_type != 'application/pdf':
        await update.message.reply_text("❌ Only PDF documents are supported.")
        return

    # Ask: Resume upload or Job submission?
    keyboard = [[
        InlineKeyboardButton("📄 Upload as Resume", callback_data=f"upload_resume_{doc.file_id}"),
        InlineKeyboardButton("💼 Submit as Job Posting", callback_data=f"submit_job_{doc.file_id}")
    ]]

    await update.message.reply_text(
        "📎 *PDF received!* What would you like to do?\n\n"
        "Choose an option below:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    user, db = get_user_by_chat(chat_id)
    db.close()

    if not user:
        await update.message.reply_text(
            "⚠️ Your account is not linked. Use `/link <code>` first.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("📸 OCR in progress on job screenshot...")

    photo = update.message.photo[-1]  # Largest version
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    from src.services.parser import DocumentParserService
    content = await DocumentParserService.parse_screenshot_ocr(bytes(image_bytes))

    if not content or len(content.strip()) < 10:
        await update.message.reply_text("❌ Could not extract enough text from the screenshot.")
        return

    await update.message.reply_text("🔍 Processing job description... This might take a moment.")
    asyncio.create_task(
        process_job_submission_task(user_id=user.id, raw_content=content)
    )


# ═══════════════════════════════════════════════════════════════════════════
# BOT APPLICATION SETUP
# ═══════════════════════════════════════════════════════════════════════════

bot_app = None
if settings.TELEGRAM_BOT_TOKEN:
    bot_app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler("help", help_command))
    bot_app.add_handler(CommandHandler("link", link_command))
    bot_app.add_handler(CommandHandler("unlink", unlink_command))
    bot_app.add_handler(CommandHandler("status", status_command))
    bot_app.add_handler(CommandHandler("drafts", drafts_command))
    bot_app.add_handler(CommandHandler("history", history_command))
    bot_app.add_handler(CommandHandler("resumes", resumes_command))
    bot_app.add_handler(CommandHandler("certificates", certificates_command))

    # Callback query handler (inline keyboard buttons)
    bot_app.add_handler(CallbackQueryHandler(callback_handler))

    # Message handlers
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    bot_app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))


def main():
    if not bot_app:
        logger.error("TELEGRAM_BOT_TOKEN not found in configurations. Exiting bot.")
        return

    logger.info("Starting Telegram Bot (Polling)...")
    bot_app.run_polling()


if __name__ == "__main__":
    main()
