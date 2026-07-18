import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Jobexa API"
    API_V1_STR: str = "/api/v1"
    JWT_SECRET_KEY: str = "supersecretkeychangeinproduction"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jobexa"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_PAIRING_CODE_EXPIRE_MINUTES: int = 10

    # NVIDIA NIM API
    NVIDIA_NIM_API_KEY: Optional[str] = None

    # Supabase Storage / S3 (Default to local folder if not configured for simple tests)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_BUCKET: str = "jobexa-documents"

    # Email Config (Gmail OAuth / SMTP fallback)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Google OAuth 2.0 Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/gmail/callback"
    ENCRYPTION_SECRET_KEY: str = "jobexa-secret-key-32-chars-long!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
