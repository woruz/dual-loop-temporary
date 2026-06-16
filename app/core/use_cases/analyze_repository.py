import logging

from app.core.entities.repository_analysis import RepositoryAnalysis
from app.core.ports.repository_ports import (
    FileExtractionPort,
    GitClonePort,
    RepositoryAnalysisRepositoryPort,
    RepositoryAnalyzerPort,
    RepositoryRepositoryPort,
)

logger = logging.getLogger(__name__)


class AnalyzeRepositoryUseCase:
    def __init__(
        self,
        repository_repo: RepositoryRepositoryPort,
        analysis_repo: RepositoryAnalysisRepositoryPort,
        git_clone: GitClonePort,
        file_extractor: FileExtractionPort,
        analyzer: RepositoryAnalyzerPort,
    ):
        self.repository_repo = repository_repo
        self.analysis_repo = analysis_repo
        self.git_clone = git_clone
        self.file_extractor = file_extractor
        self.analyzer = analyzer

    async def execute(self, user_id: int, repository_id: int) -> RepositoryAnalysis:
        logger.info("[RepositoryAnalysis] Starting analysis for repository_id=%s", repository_id)

        repository = await self.repository_repo.get_by_id_and_user(repository_id, user_id)
        if not repository:
            raise ValueError(f"Repository {repository_id} not found for user {user_id}")

        existing = await self.analysis_repo.get_by_repository_id(repository_id)
        if existing:
            logger.info(
                "[RepositoryAnalysis] Returning cached analysis for repository_id=%s",
                repository_id,
            )
            return existing

        repo_path: str | None = None
        try:
            logger.info(
                "[RepositoryAnalysis] Cloning repository %s (%s)",
                repository.repo_name,
                repository.repo_url,
            )
            repo_path = await self.git_clone.clone(repository.repo_url)
            logger.info("[RepositoryAnalysis] Clone completed at %s", repo_path)

            logger.info("[RepositoryAnalysis] Detecting project type and extracting files...")
            extraction = await self.file_extractor.extract(repo_path)
            logger.info(
                "[RepositoryAnalysis] Project Type: %s | Files Extracted: %d | Context Length: %d",
                extraction.project_type,
                extraction.file_count,
                len(extraction.context),
            )

            logger.info("[RepositoryAnalysis] Sending to Groq for %s...", repository.repo_name)
            result = await self.analyzer.analyze(
                repository.repo_name,
                extraction.project_type,
                extraction.context,
            )
            logger.info(
                "[RepositoryAnalysis] Groq analysis received — overall_score=%.1f",
                result.overall_score,
            )

            logger.info("[RepositoryAnalysis] Saving analysis to database...")
            analysis = await self.analysis_repo.create(
                repository_id=repository_id,
                overall_score=result.overall_score,
                security_score=result.security_score,
                performance_score=result.performance_score,
                maintainability_score=result.maintainability_score,
                architecture_score=result.architecture_score,
                strengths=result.strengths,
                weaknesses=result.weaknesses,
                recommendations=result.recommendations,
                project_type=extraction.project_type,
                files_analyzed=extraction.files_analyzed,
            )
            logger.info(
                "[RepositoryAnalysis] Analysis saved — analysis_id=%s repository_id=%s project_type=%s files=%d",
                analysis.id,
                repository_id,
                analysis.project_type,
                len(analysis.files_analyzed),
            )
            return analysis
        except Exception:
            logger.exception(
                "[RepositoryAnalysis] Analysis failed for repository_id=%s",
                repository_id,
            )
            raise
        finally:
            if repo_path:
                await self.git_clone.cleanup(repo_path)
                logger.info("[RepositoryAnalysis] Temporary clone cleaned up")
