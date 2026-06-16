import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.entities.user import User
from app.core.use_cases.analyze_repository import AnalyzeRepositoryUseCase
from app.core.use_cases.create_repository import CreateRepositoryUseCase
from app.core.use_cases.repository_queries import (
    GetRepositoryAnalysisUseCase,
    GetRepositoryUseCase,
    ListRepositoriesUseCase,
)
from app.server.dependencies import (
    get_analyze_repository_use_case,
    get_create_repository_use_case,
    get_current_active_user,
    get_get_repository_analysis_use_case,
    get_get_repository_use_case,
    get_list_repositories_use_case,
)
from app.server.schemas.repository_schemas import (
    CreateRepositoryRequest,
    RepositoryAnalysisResponse,
    RepositoryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["Repository Analysis"])


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    body: CreateRepositoryRequest,
    current_user: User = Depends(get_current_active_user),
    use_case: CreateRepositoryUseCase = Depends(get_create_repository_use_case),
):
    try:
        repository = await use_case.execute(
            user_id=current_user.id,
            repo_url=str(body.repo_url),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RepositoryResponse(
        id=repository.id,
        user_id=repository.user_id,
        repo_name=repository.repo_name,
        repo_url=repository.repo_url,
        created_at=repository.created_at,
    )


@router.post(
    "/analyze/{repo_id}",
    response_model=RepositoryAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_repository(
    repo_id: int,
    current_user: User = Depends(get_current_active_user),
    use_case: AnalyzeRepositoryUseCase = Depends(get_analyze_repository_use_case),
):
    try:
        analysis = await use_case.execute(user_id=current_user.id, repository_id=repo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Repository analysis failed for repo_id=%s: %s", repo_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return RepositoryAnalysisResponse(
        id=analysis.id,
        repository_id=analysis.repository_id,
        overall_score=analysis.overall_score,
        security_score=analysis.security_score,
        performance_score=analysis.performance_score,
        maintainability_score=analysis.maintainability_score,
        architecture_score=analysis.architecture_score,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        recommendations=analysis.recommendations,
        project_type=analysis.project_type,
        files_analyzed=analysis.files_analyzed,
        created_at=analysis.created_at,
    )


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    current_user: User = Depends(get_current_active_user),
    use_case: ListRepositoriesUseCase = Depends(get_list_repositories_use_case),
):
    repositories = await use_case.execute(user_id=current_user.id)
    return [
        RepositoryResponse(
            id=repo.id,
            user_id=repo.user_id,
            repo_name=repo.repo_name,
            repo_url=repo.repo_url,
            created_at=repo.created_at,
        )
        for repo in repositories
    ]


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: int,
    current_user: User = Depends(get_current_active_user),
    use_case: GetRepositoryUseCase = Depends(get_get_repository_use_case),
):
    try:
        repository = await use_case.execute(user_id=current_user.id, repository_id=repo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RepositoryResponse(
        id=repository.id,
        user_id=repository.user_id,
        repo_name=repository.repo_name,
        repo_url=repository.repo_url,
        created_at=repository.created_at,
    )


@router.get("/{repo_id}/analysis", response_model=RepositoryAnalysisResponse)
async def get_repository_analysis(
    repo_id: int,
    current_user: User = Depends(get_current_active_user),
    use_case: GetRepositoryAnalysisUseCase = Depends(get_get_repository_analysis_use_case),
):
    try:
        analysis = await use_case.execute(user_id=current_user.id, repository_id=repo_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return RepositoryAnalysisResponse(
        id=analysis.id,
        repository_id=analysis.repository_id,
        overall_score=analysis.overall_score,
        security_score=analysis.security_score,
        performance_score=analysis.performance_score,
        maintainability_score=analysis.maintainability_score,
        architecture_score=analysis.architecture_score,
        strengths=analysis.strengths,
        weaknesses=analysis.weaknesses,
        recommendations=analysis.recommendations,
        project_type=analysis.project_type,
        files_analyzed=analysis.files_analyzed,
        created_at=analysis.created_at,
    )
