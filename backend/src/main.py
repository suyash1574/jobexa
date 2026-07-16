from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os

from src.config import settings
from src.api import auth, drafts, documents, analytics

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("jobexa")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register routes
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(drafts.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

# Mount static files for local PDF storage
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return {"message": "Jobexa API is active. Pair with Telegram Bot or use the Web Dashboard."}

@app.post("/webhook/telegram")
async def telegram_webhook(update_dict: dict):
    logger.info(f"Received Telegram webhook update payload: {update_dict}")
    from bot import bot_app
    from telegram import Update
    if bot_app:
        try:
            update = Update.de_json(update_dict, bot_app.bot)
            # Ensure bot application is initialized and started before processing updates
            if not bot_app.running:
                logger.info("Initializing and starting Telegram bot application...")
                await bot_app.initialize()
                await bot_app.start()
            logger.info("Processing update via process_update...")
            await bot_app.process_update(update)
            logger.info("Telegram update processed successfully.")
        except Exception as e:
            import traceback
            logger.error(f"Error processing telegram webhook: {e}")
            logger.error(traceback.format_exc())
    else:
        logger.warning("Telegram Bot Application is not initialized (check TELEGRAM_BOT_TOKEN environment variable). Webhook request skipped.")
    return {"status": "ok"}
