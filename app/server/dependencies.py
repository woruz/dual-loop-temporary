"""
LOCATION: app/dependencies.py
 
WHY HERE: This is your Dependency Injection (DI) container.
It's where you WIRE together the ports and their implementations.
 
FastAPI's Depends() system calls these functions to inject the right
implementation wherever needed. Swap an implementation in ONE place.
 
Example: To swap SQLAlchemy → MongoDB, only change get_user_repository().
"""
from functools import lru_cache
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.adapters.database import get_db
from app.infrastructure.adapters.user_repository import SQLAlchemyUserRepository
from app.infrastructure.adapters.github_oauth_adapter import HttpxGithubOAuthAdapter
from app.infrastructure.adapters.token_service import JWTTokenService
from app.core.use_cases.auth_use_cases import GithubAuthUseCase
from app.core.entities.user import User

 
# HTTP Bearer token extractor for protected routes
bearer_scheme = HTTPBearer(auto_error=False)


# ─── Singleton Factories ──────────────────────────────────────────────────────
# lru_cache ensures these are created once and reused (they're stateless)

@lru_cache(maxsize = 1)
def get_github_oauth_adapter()->HttpxGithubOAuthAdapter:
    """Stateless GitHub HTTP client — safe to cache."""
    return HttpxGithubOAuthAdapter()

@lru_cache(maxsize=1)
def get_token_service()-> JWTTokenService:
    """Stateless JWT service — safe to cache."""
    return JWTTokenService()

# ─── Request-scoped Factories ─────────────────────────────────────────────────
# These are created fresh per request (DB session is per-request)

def get_user_repository(db:AsyncSession=Depends(get_db))->SQLAlchemyUserRepository:      
    """New repository per request, bound to the request's DB session."""
    return SQLAlchemyUserRepository(get_db)

def get_auth_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    github_oauth: HttpxGithubOAuthAdapter = Depends(get_github_oauth_adapter),
    token_service: JWTTokenService = Depends(get_token_service),
) -> GithubAuthUseCase:
    """Wire together the use-case with its dependencies."""
    return GithubAuthUseCase(
        user_repo=user_repo,
        github_oauth=github_oauth,
        token_service=token_service,
    )

##Auth Middlewear____________________
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_use_case: GithubAuthUseCase = Depends(get_auth_use_case),
) -> User:
    """
    FastAPI dependency for protected routes.
    Usage: current_user: User = Depends(get_current_user)
 
    Extracts Bearer token from Authorization header,
    validates it, and returns the User entity.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
 
    try:
        user = await auth_use_case.get_current_user(credentials.credentials)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
async def get_current_active_user(
        current_user:User = Depends(get_current_user),



)-> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is Deactivated",
        )
    return current_user