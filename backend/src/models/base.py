from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import settings

import logging
logger = logging.getLogger("jobexa.database")

db_url = settings.DATABASE_URL
engine = None
db_connection_error = None

# If no DB URL is set, points to localhost, or contains placeholder text, use SQLite for local compatibility
if not db_url or "localhost:5432" in db_url or "[YOUR-PASSWORD]" in db_url or "YOUR_" in db_url:
    logger.info("Local environment detected. Defaulting to local SQLite file database (jobexa.db).")
    db_url = "sqlite:///../jobexa.db"
    db_connection_error = "Using local SQLite database."

try:
    connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
    engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info(f"Database connection verified: {db_url.split('@')[-1] if '@' in db_url else db_url}")
except Exception as e:
    db_connection_error = str(e)
    logger.error(f"Failed to connect to database {db_url} due to: {e}. Falling back to SQLite.")
    db_url = "sqlite:///../jobexa.db"
    engine = create_engine(db_url, pool_pre_ping=True, connect_args={"check_same_thread": False})

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()

def init_db():
    """Import all models and create tables if they do not exist."""
    import src.models.user
    import src.models.resume
    import src.models.application
    Base.metadata.create_all(bind=engine)

init_db()

# Dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
