from app.core.entities.repository import Repository
from app.core.entities.repository_analysis import RepositoryAnalysis
from app.core.ports.repository_ports import (
    RepositoryAnalysisRepositoryPort,
    RepositoryRepositoryPort,
)


class ListRepositoriesUseCase:
    def __init__(self, repository_repo: RepositoryRepositoryPort):
        self.repository_repo = repository_repo

    async def execute(self, user_id: int) -> list[Repository]:
        return await self.repository_repo.list_by_user(user_id)


class GetRepositoryUseCase:
    def __init__(self, repository_repo: RepositoryRepositoryPort):
        self.repository_repo = repository_repo

    async def execute(self, user_id: int, repository_id: int) -> Repository:
        repository = await self.repository_repo.get_by_id_and_user(repository_id, user_id)
        if not repository:
            raise ValueError(f"Repository {repository_id} not found for user {user_id}")
        return repository


class GetRepositoryAnalysisUseCase:
    def __init__(
        self,
        repository_repo: RepositoryRepositoryPort,
        analysis_repo: RepositoryAnalysisRepositoryPort,
    ):
        self.repository_repo = repository_repo
        self.analysis_repo = analysis_repo

    async def execute(self, user_id: int, repository_id: int) -> RepositoryAnalysis:
        repository = await self.repository_repo.get_by_id_and_user(repository_id, user_id)
        if not repository:
            raise ValueError(f"Repository {repository_id} not found for user {user_id}")

        analysis = await self.analysis_repo.get_by_repository_id(repository_id)
        if not analysis:
            raise ValueError(f"Analysis not found for repository {repository_id}")
        return analysis
