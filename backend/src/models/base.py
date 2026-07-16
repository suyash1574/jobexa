from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import settings

import logging
logger = logging.getLogger("jobexa.database")

db_url = settings.DATABASE_URL
engine = None

# If no DB URL is set or it points to localhost (default config), use SQLite for Render compatibility
if not db_url or "localhost:5432" in db_url:
    logger.warning("No production DATABASE_URL configured or localhost detected. Defaulting to local SQLite file database.")
    db_url = "sqlite:///../jobexa.db"

try:
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info(f"Database connection verified: {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    logger.error(f"Failed to connect to database {db_url} due to: {e}. Falling back to SQLite.")
    db_url = "sqlite:///../jobexa.db"
    engine = create_engine(db_url, pool_pre_ping=True, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
