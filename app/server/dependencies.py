import os
import logging
import socket
from uuid import UUID
from urllib.parse import urlparse
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

load_dotenv()

from app.core.ports.auth_repo import AuthRepo
from app.core.ports.password_hasher import IPasswordHasher
from app.core.ports.token_generator import ITokenGenerator
from app.core.ports.oauth_port import OAuthPort

from app.infrastructure.adapters.postgres_auth_repo import PostgresAuthRepo
from app.infrastructure.adapters.github_oauth import GitHubOAuth
from app.infrastructure.adapters.bcrypt_hasher import BcryptHasher
from app.infrastructure.adapters.jwt_generator import JWTGenerator
from app.infrastructure.adapters.postgres_webhook_repo import PostgresWebhookRepo
from app.core.use_cases.process_webhook import ProcessWebhookUseCase

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
    logger.info(f"Database successfully Connected")

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

# ── Webhook dependencies ──────────────────────────────────────────
async def get_webhook_repo(db: AsyncSession = Depends(get_db)) -> PostgresWebhookRepo:
    return PostgresWebhookRepo(db)

def get_process_webhook_use_case(
    repo: PostgresWebhookRepo = Depends(get_webhook_repo)
) -> ProcessWebhookUseCase:
    return ProcessWebhookUseCase(repo)

# ── Auth guard ────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    access_token: str | None = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    repo: AuthRepo = Depends(get_auth_repo),
    token_generator: ITokenGenerator = Depends(get_token_generator),
):
    token = access_token
    print(f"Access token: {access_token}")  # Debug log for cookie token
    if not token and credentials:
        token = credentials.credentials
        
    print(f"Access token from Cookie: {credentials}")  # Debug log for cookie token
    print("I am here")
    if not token:
        logger.warning("Authentication failed: Missing access token in Cookie and Authorization header.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
        
    payload = token_generator.verify_token(token)
    print(f"Token payload: {payload}")  # Debug log to inspect token contents
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
        
    # Bind verification status from token payload if present, bypassing further DB queries
    if payload.get("is_verified_forjournal"):
        user.is_verified_forjournal = True

    logger.debug(f"User '{user.email}' authenticated successfully.")
    return user

# ── Journal and Analysis Dependencies ──────────────────────────────
from app.core.ports.journal_repo import JournalRepositoryPort
from app.core.ports.analysis_repo import AnalysisRepositoryPort
from app.core.ports.journal_llm import JournalLLMPort
from app.infrastructure.adapters.postgres_journal_repo import PostgresJournalRepo
from app.infrastructure.adapters.postgres_analysis_repo import PostgresAnalysisRepo
from app.infrastructure.adapters.groq_journal_llm_adapter import GroqJournalLLMAdapter

async def get_journal_repo(db: AsyncSession = Depends(get_db)) -> JournalRepositoryPort:
    return PostgresJournalRepo(db)

async def get_analysis_repo(db: AsyncSession = Depends(get_db)) -> AnalysisRepositoryPort:
    return PostgresAnalysisRepo(db)

def get_journal_llm_adapter() -> JournalLLMPort:
    return GroqJournalLLMAdapter()