import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

Base = declarative_base()

load_dotenv(dotenv_path="f:/dual-loop-temporary/.env")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.infrastructure.adapters.database")

DATABASE_URL = os.getenv("DATABASE_URL", "")
try:
    if DATABASE_URL.startswith("postgresql"):
        logger.info(f"[Database] Connection URL detected for PostgreSQL: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            logger.info("[Database] Successfully connected to PostgreSQL instance.")
    else:
        raise ValueError("DATABASE_URL is empty or not configured as a postgresql connection string.")
except Exception as e:
    # Safe fallback to a local SQLite database for development/offline testing
    logger.warning(f"[Database Warning] PostgreSQL connection failed: {e}")
    logger.info("[Database Info] Falling back to SQLite dialect (sqlite:///./dualloop.db)")
    DATABASE_URL = "sqlite:///./dualloop.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Configured SQLAlchemy Session generator
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes database tables.
    Importing the models dynamically inside this helper avoids circular dependency 
    loops during startup, as the models package references Base back from this module.
    """
    from . import models
    logger.info(f"[Database] Creating schemas/tables for database URL: {DATABASE_URL}")
    Base.metadata.create_all(bind=engine)

# Auto-initialize database tables on first module import
init_db()
