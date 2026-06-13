import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from app.server.routers.auth import router as auth_router
from app.server.routers.webhook import router as webhook_router
from app.server.dependencies import engine

# Configure logging format and level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.server.main")




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once on startup — creates tables if they don't exist
    logger.info("Database tables initialization started.")
    try:
        async with engine.begin() as conn:
            # Create users table (compatible with PostgreSQL)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255),
                    full_name VARCHAR(255),
                    is_verified_forjournal BOOLEAN DEFAULT FALSE,
                    goal TEXT,
                    experience TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Check existing columns in the users table
            res = await conn.execute(text("SELECT * FROM users LIMIT 0"))
            existing_cols = set(res.keys())

            # Dynamically add missing columns if they do not exist (for existing tables)
            for col, col_type in [
                ("full_name", "VARCHAR(255)"),
                ("goal", "TEXT"),
                ("experience", "TEXT"),
                ("is_verified_forjournal", "BOOLEAN DEFAULT FALSE")
            ]:
                if col not in existing_cols:
                    try:
                        await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {col_type}"))
                        logger.info(f"Database: Added column '{col}' to table 'users'.")
                    except Exception as alter_err:
                        logger.warning(f"Database: Failed to add column '{col}' to table 'users': {alter_err}")
            # Create oauth_profiles table (compatible with PostgreSQL)
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
            # Create repos table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS repos (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    owner_username VARCHAR(255) NOT NULL,
                    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Create commits table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS commits (
                    id VARCHAR(36) PRIMARY KEY,
                    repo_id VARCHAR(36) REFERENCES repos(id) ON DELETE CASCADE NOT NULL,
                    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
                    pusher_username VARCHAR(255) NOT NULL,
                    branch VARCHAR(255) NOT NULL,
                    message JSON NOT NULL,
                    total_commit INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL
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

# Retrieve allowed CORS origins dynamically from the environment
cors_origins_env = os.getenv("CORS_ORIGINS")
if cors_origins_env:
    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    origins = [
        "https://93qrwwjq-5174.inc1.devtunnels.ms",
        "http://localhost:3000",   
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the routers
app.include_router(auth_router)
app.include_router(webhook_router)

@app.get("/test")
async def serve_test_page():
    return FileResponse("test_frontend.html")