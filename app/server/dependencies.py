import os
import logging
import socket
from uuid import UUID
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Load environment variables from .env file
load_dotenv()

from app.core.ports.auth_repo import AuthRepo
from app.core.ports.password_hasher import IPasswordHasher
from app.core.ports.token_generator import ITokenGenerator
from app.core.ports.oauth_port import OAuthPort

from app.infrastructure.adapters.postgres_auth_repo import PostgresAuthRepo
from app.infrastructure.adapters.github_oauth import GitHubOAuth
from app.infrastructure.adapters.bcrypt_hasher import BcryptHasher
from app.infrastructure.adapters.jwt_generator import JWTGenerator

logger = logging.getLogger("app.server.dependencies")

# ── DB configuration & setup with dynamic fallback ─────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")
USE_SQLITE = True

if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+asyncpg://"):
    try:
        # Parse the host and port from connection string
        parsed = urlparse(DATABASE_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        
        # Test if the socket port is open/reachable (timeout = 1s)
        with socket.create_connection((host, port), timeout=1.0):
            pass
        logger.info(f"Database: PostgreSQL instance detected active at {host}:{port}")
        USE_SQLITE = False
    except Exception as e:
        logger.warning(f"Database: PostgreSQL socket check failed at {host}:{port} ({e}). Falling back to SQLite.")
else:
    logger.warning("Database: No PostgreSQL URL found in environment variables. Falling back to SQLite.")

if USE_SQLITE:
    DATABASE_URL_ASYNC = "sqlite+aiosqlite:///./dualloop.db"
    logger.info(f"Database: Configured SQLite async database URL: {DATABASE_URL_ASYNC}")
else:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL_ASYNC = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL_ASYNC = DATABASE_URL
    logger.info(f"Database: Configured PostgreSQL async database URL: {DATABASE_URL_ASYNC}")

try:
    engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
except Exception as e:
    logger.critical(f"Database: Failed to initialize engine: {e}", exc_info=True)
    raise

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error yielding DB session: {e}", exc_info=True)
            raise

# ── Repo / adapter deps ───────────────────────────────────────────
async def get_auth_repo(db: AsyncSession = Depends(get_db)) -> AuthRepo:
    return PostgresAuthRepo(db)

def get_github_oauth() -> OAuthPort:
    client_id = os.getenv("GITHUB_CLIENT_ID", "")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        logger.error("GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET is missing from environment!")
    return GitHubOAuth(
        client_id=client_id,
        client_secret=client_secret,
    )

def get_password_hasher() -> IPasswordHasher:
    return BcryptHasher()

def get_token_generator() -> ITokenGenerator:
    return JWTGenerator()

# ── Auth guard ────────────────────────────────────────────────────
_bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    repo: AuthRepo = Depends(get_auth_repo),
    token_generator: ITokenGenerator = Depends(get_token_generator),
):
    token = credentials.credentials
    payload = token_generator.verify_token(token)
    
    if not payload:
        logger.warning("Authentication failed: Invalid or expired access token.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    
    sub = payload.get("sub")
    if not sub:
        logger.warning("Authentication failed: Access token missing 'sub' claim.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        
    try:
        user_id = UUID(sub)
    except ValueError:
        logger.warning(f"Authentication failed: 'sub' claim is not a valid UUID string: {sub}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    
    user = await repo.get_user_by_id(user_id)
    if not user:
        logger.warning(f"Authentication failed: User id '{user_id}' not found in database.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
        
    logger.debug(f"User '{user.email}' authenticated successfully.")
    return user