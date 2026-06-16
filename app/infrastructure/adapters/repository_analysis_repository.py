import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.repository_analysis import RepositoryAnalysis
from app.core.ports.repository_ports import RepositoryAnalysisRepositoryPort
from app.infrastructure.adapters.repository_models import RepositoryAnalysisModel


def _loads_list(value: str) -> list[str]:
    parsed = json.loads(value)
    return [str(item) for item in parsed]


def _dumps_list(items: list[str]) -> str:
    return json.dumps(items)


def _model_to_entity(model: RepositoryAnalysisModel) -> RepositoryAnalysis:
    return RepositoryAnalysis(
        id=model.id,
        repository_id=model.repository_id,
        overall_score=model.overall_score,
        security_score=model.security_score,
        performance_score=model.performance_score,
        maintainability_score=model.maintainability_score,
        architecture_score=model.architecture_score,
        strengths=_loads_list(model.strengths),
        weaknesses=_loads_list(model.weaknesses),
        recommendations=_loads_list(model.recommendations),
        project_type=model.project_type,
        files_analyzed=_loads_list(model.files_analyzed),
        created_at=model.created_at,
    )


class SQLAlchemyRepositoryAnalysisRepository(RepositoryAnalysisRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

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
        model = RepositoryAnalysisModel(
            repository_id=repository_id,
            overall_score=overall_score,
            security_score=security_score,
            performance_score=performance_score,
            maintainability_score=maintainability_score,
            architecture_score=architecture_score,
            strengths=_dumps_list(strengths),
            weaknesses=_dumps_list(weaknesses),
            recommendations=_dumps_list(recommendations),
            project_type=project_type,
            files_analyzed=_dumps_list(files_analyzed),
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def get_by_repository_id(
        self, repository_id: int
    ) -> Optional[RepositoryAnalysis]:
        result = await self.db.execute(
            select(RepositoryAnalysisModel).where(
                RepositoryAnalysisModel.repository_id == repository_id
            )
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
