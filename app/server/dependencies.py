"""
LOCATION: app/dependencies.py
 
WHY HERE: This is your Dependency Injection (DI) container.
It's where you WIRE together the ports and their implementations.
 
FastAPI's Depends() system calls these functions to inject the right
implementation wherever needed. Swap an implementation in ONE place.
 
Example: To swap SQLAlchemy → MongoDB, only change get_user_repository().
"""
from functools import lru_cache
import logging

from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.server.auth_config import get_dev_user, is_development

logger = logging.getLogger(__name__)

from app.infrastructure.adapters.database import get_db
from app.infrastructure.adapters.user_repository import SQLAlchemyUserRepository
from app.infrastructure.adapters.github_oauth_adapter import HttpxGithubOAuthAdapter
from app.infrastructure.adapters.token_service import JWTTokenService
from app.core.use_cases.auth_use_cases import GithubAuthUseCase
from app.core.use_cases.analyze_journal import AnalyzeJournalUseCase
from app.core.use_cases.create_goal import CreateGoalUseCase
from app.core.use_cases.create_journal import CreateJournalUseCase
from app.core.entities.user import User
from app.infrastructure.adapters.goal_repository import SQLAlchemyGoalRepository
from app.infrastructure.adapters.journal_repository import SQLAlchemyJournalRepository
from app.infrastructure.adapters.journal_analysis_repository import SQLAlchemyJournalAnalysisRepository
from app.infrastructure.adapters.groq_llm_adapter import GroqLLMAdapter
from app.infrastructure.adapters.groq_repository_analyzer import GroqRepositoryAnalyzer
from app.infrastructure.adapters.git_clone_service import GitCloneService
from app.infrastructure.adapters.file_extraction_service import FileExtractionService
from app.infrastructure.adapters.repository_repository import SQLAlchemyRepositoryRepository
from app.infrastructure.adapters.repository_analysis_repository import (
    SQLAlchemyRepositoryAnalysisRepository,
)
from app.core.use_cases.analyze_repository import AnalyzeRepositoryUseCase
from app.core.use_cases.create_repository import CreateRepositoryUseCase
from app.core.use_cases.repository_queries import (
    GetRepositoryAnalysisUseCase,
    GetRepositoryUseCase,
    ListRepositoriesUseCase,
)

 
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
    return SQLAlchemyUserRepository(db)

def get_auth_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    github_oauth: HttpxGithubOAuthAdapter = Depends(get_github_oauth_adapter),
    token_service: JWTTokenService = Depends(get_token_service),
) -> GithubAuthUseCase:
    """Wire together the use-case with its dependencies."""
    return GithubAuthUseCase(
        user_repo=user_repo,
        oauth_port=github_oauth,
        token_service=token_service,
    )

##Auth Middlewear____________________
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_use_case: GithubAuthUseCase = Depends(get_auth_use_case),
) -> User:
    """
    FastAPI dependency for protected routes.
    In development mode (ENVIRONMENT=development), returns a mock user
    so Swagger testing works without OAuth. Production requires JWT.
    """
    if is_development():
        logger.debug("Development mode: returning mock authenticated user")
        return get_dev_user()

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


# ─── Daily Journal Factories ──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_groq_llm_adapter() -> GroqLLMAdapter:
    return GroqLLMAdapter()


def get_goal_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyGoalRepository:
    return SQLAlchemyGoalRepository(db)


def get_journal_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyJournalRepository:
    return SQLAlchemyJournalRepository(db)


def get_journal_analysis_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyJournalAnalysisRepository:
    return SQLAlchemyJournalAnalysisRepository(db)


def get_create_goal_use_case(
    goal_repo: SQLAlchemyGoalRepository = Depends(get_goal_repository),
) -> CreateGoalUseCase:
    return CreateGoalUseCase(goal_repo=goal_repo)


def get_create_journal_use_case(
    journal_repo: SQLAlchemyJournalRepository = Depends(get_journal_repository),
    goal_repo: SQLAlchemyGoalRepository = Depends(get_goal_repository),
) -> CreateJournalUseCase:
    return CreateJournalUseCase(journal_repo=journal_repo, goal_repo=goal_repo)


def get_analyze_journal_use_case(
    journal_repo: SQLAlchemyJournalRepository = Depends(get_journal_repository),
    goal_repo: SQLAlchemyGoalRepository = Depends(get_goal_repository),
    analysis_repo: SQLAlchemyJournalAnalysisRepository = Depends(get_journal_analysis_repository),
    llm: GroqLLMAdapter = Depends(get_groq_llm_adapter),
) -> AnalyzeJournalUseCase:
    return AnalyzeJournalUseCase(
        journal_repo=journal_repo,
        goal_repo=goal_repo,
        analysis_repo=analysis_repo,
        llm=llm,
    )


# ─── Repository Analysis Factories ────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_groq_repository_analyzer() -> GroqRepositoryAnalyzer:
    return GroqRepositoryAnalyzer()


@lru_cache(maxsize=1)
def get_git_clone_service() -> GitCloneService:
    return GitCloneService()


@lru_cache(maxsize=1)
def get_file_extraction_service() -> FileExtractionService:
    return FileExtractionService()


def get_repository_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyRepositoryRepository:
    return SQLAlchemyRepositoryRepository(db)


def get_repository_analysis_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyRepositoryAnalysisRepository:
    return SQLAlchemyRepositoryAnalysisRepository(db)


def get_create_repository_use_case(
    repository_repo: SQLAlchemyRepositoryRepository = Depends(get_repository_repository),
) -> CreateRepositoryUseCase:
    return CreateRepositoryUseCase(repository_repo=repository_repo)


def get_analyze_repository_use_case(
    repository_repo: SQLAlchemyRepositoryRepository = Depends(get_repository_repository),
    analysis_repo: SQLAlchemyRepositoryAnalysisRepository = Depends(
        get_repository_analysis_repository
    ),
    git_clone: GitCloneService = Depends(get_git_clone_service),
    file_extractor: FileExtractionService = Depends(get_file_extraction_service),
    analyzer: GroqRepositoryAnalyzer = Depends(get_groq_repository_analyzer),
) -> AnalyzeRepositoryUseCase:
    return AnalyzeRepositoryUseCase(
        repository_repo=repository_repo,
        analysis_repo=analysis_repo,
        git_clone=git_clone,
        file_extractor=file_extractor,
        analyzer=analyzer,
    )


def get_list_repositories_use_case(
    repository_repo: SQLAlchemyRepositoryRepository = Depends(get_repository_repository),
) -> ListRepositoriesUseCase:
    return ListRepositoriesUseCase(repository_repo=repository_repo)


def get_get_repository_use_case(
    repository_repo: SQLAlchemyRepositoryRepository = Depends(get_repository_repository),
) -> GetRepositoryUseCase:
    return GetRepositoryUseCase(repository_repo=repository_repo)


def get_get_repository_analysis_use_case(
    repository_repo: SQLAlchemyRepositoryRepository = Depends(get_repository_repository),
    analysis_repo: SQLAlchemyRepositoryAnalysisRepository = Depends(
        get_repository_analysis_repository
    ),
) -> GetRepositoryAnalysisUseCase:
    return GetRepositoryAnalysisUseCase(
        repository_repo=repository_repo,
        analysis_repo=analysis_repo,
    )