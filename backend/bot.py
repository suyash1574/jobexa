import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import asyncio

# Setup sys.path to backend directory
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import settings
from src.models.base import SessionLocal
from src.models.user import User
from src.services.tasks import process_job_submission_task

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("jobexa.bot")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "Welcome to Jobexa! 🤖 Your personal AI career assistant.\n\n"
        "Please link your Telegram session to your Web Dashboard account to get started.\n"
        "Run `/link <code>` using the pairing code generated in your Web Dashboard Profile settings."
    )
    await update.message.reply_text(message)

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Please specify the pairing code. Example: `/link 123456`.")
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
            await update.message.reply_text("✅ Accounts paired successfully! You can now send job posts here.")
        else:
            await update.message.reply_text("❌ Invalid or expired pairing code. Please generate a new one on the dashboard.")
    except Exception as e:
        logger.error(f"Error pairing Telegram account: {str(e)}")
        await update.message.reply_text("❌ An error occurred while pairing your account. Please try again later.")
    finally:
        db.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.effective_chat.id)
    
    # 1. Verify user is linked
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
    db.close()

    if not user:
        await update.message.reply_text("⚠️ Your account is not linked. Use `/link <code>` first.")
        return

    content = ""
    # Check if text message
    if update.message.text:
        content = update.message.text
    # Check if document (PDF)
    elif update.message.document:
        doc = update.message.document
        if doc.mime_type == 'application/pdf':
            await update.message.reply_text("📥 Downloading PDF job description...")
            file = await context.bot.get_file(doc.file_id)
            pdf_bytes = await file.download_as_bytearray()
            # Parse text from PDF bytes
            from src.services.parser import DocumentParserService
            content = DocumentParserService.parse_pdf(bytes(pdf_bytes))
        else:
            await update.message.reply_text("❌ Only PDF documents are supported currently.")
            return
    # Check if photo/screenshot
    elif update.message.photo:
        await update.message.reply_text("📥 OCR in progress on job screenshot...")
        photo = update.message.photo[-1] # Largest version
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        from src.services.parser import DocumentParserService
        content = await DocumentParserService.parse_screenshot_ocr(bytes(image_bytes))

    if not content or len(content.strip()) < 10:
        await update.message.reply_text("❌ Could not extract enough text from the posting. Please paste the job description directly.")
        return

    await update.message.reply_text("🔍 Processing job description... This might take a moment.")
    
    # Launch background parsing task
    asyncio.create_task(
        process_job_submission_task(
            user_id=user.id,
            raw_content=content
        )
    )

def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in configurations. Exiting bot.")
        return

    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("link", link_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))

    logger.info("Starting Telegram Bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
