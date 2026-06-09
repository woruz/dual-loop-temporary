import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text

# Configure logging format and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.server.main")

from app.server.routers.auth import router as auth_router
from app.server.dependencies import engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup — creates tables if they don't exist
    logger.info("Database tables initialization started.")
    try:
        async with engine.begin() as conn:
            # Create users table (compatible with PostgreSQL and SQLite)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255),
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Create oauth_profiles table (compatible with PostgreSQL and SQLite)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS oauth_profiles (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
                    provider VARCHAR(50) NOT NULL,
                    provider_user_id VARCHAR(255) NOT NULL,
                    username VARCHAR(255),
                    avatar_url TEXT,
                    UNIQUE(provider, provider_user_id)
                )
            """))
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.critical(f"Database initialization failed: {e}", exc_info=True)
        raise
        
    yield
    # Runs on shutdown (cleanup if needed)
    logger.info("Shutting down application...")

app = FastAPI(
    title="Dual-Loop User Authentication Service",
    description="Hexagonal architecture implementation for user signup, signin, and GitHub OAuth.",
    version="1.0.0",
    lifespan=lifespan
)

# Mount only the auth router
app.include_router(auth_router)