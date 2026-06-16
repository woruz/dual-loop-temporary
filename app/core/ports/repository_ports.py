from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.core.entities.extraction_result import ExtractionResult
from app.core.entities.repository import Repository
from app.core.entities.repository_analysis import RepositoryAnalysis


@dataclass
class RepositoryAnalysisResult:
    overall_score: float
    security_score: float
    performance_score: float
    maintainability_score: float
    architecture_score: float
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


class RepositoryRepositoryPort(ABC):
    @abstractmethod
    async def create(self, user_id: int, repo_name: str, repo_url: str) -> Repository:
        ...

    @abstractmethod
    async def get_by_id(self, repository_id: int) -> Optional[Repository]:
        ...

    @abstractmethod
    async def get_by_id_and_user(
        self, repository_id: int, user_id: int
    ) -> Optional[Repository]:
        ...

    @abstractmethod
    async def list_by_user(self, user_id: int) -> list[Repository]:
        ...


class RepositoryAnalysisRepositoryPort(ABC):
    @abstractmethod
    async def create(
        self,
        repository_id: int,
        overall_score: float,
        security_score: float,
        performance_score: float,
        maintainability_score: float,
        architecture_score: float,
        strengths: list[str],
        weaknesses: list[str],
        recommendations: list[str],
        project_type: str,
        files_analyzed: list[str],
    ) -> RepositoryAnalysis:
        ...

    @abstractmethod
    async def get_by_repository_id(
        self, repository_id: int
    ) -> Optional[RepositoryAnalysis]:
        ...


class GitClonePort(ABC):
    @abstractmethod
    async def clone(self, repo_url: str) -> str:
        """Clone repository into a temporary directory and return its path."""
        ...

    @abstractmethod
    async def cleanup(self, repo_path: str) -> None:
        """Remove temporary clone directory."""
        ...


class FileExtractionPort(ABC):
    @abstractmethod
    async def extract(self, repo_path: str) -> ExtractionResult:
        """Detect project type and build structured analysis context."""
        ...

    @abstractmethod
    async def extract_context(self, repo_path: str) -> str:
        """Backward-compatible helper returning only the context string."""
        ...


class RepositoryAnalyzerPort(ABC):
    @abstractmethod
    async def analyze(
        self, repo_name: str, project_type: str, context: str
    ) -> RepositoryAnalysisResult:
        ...
