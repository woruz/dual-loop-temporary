from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.journal_analysis import JournalAnalysis
from app.core.ports.journal_ports import JournalAnalysisRepositoryPort
from app.infrastructure.adapters.journal_models import JournalAnalysisModel


def _model_to_entity(model: JournalAnalysisModel) -> JournalAnalysis:
    return JournalAnalysis(
        id=model.id,
        journal_id=model.journal_id,
        productivity_score=model.productivity_score,
        sentiment_score=model.sentiment_score,
        goal_alignment_score=model.goal_alignment_score,
        risk_level=model.risk_level,
        feedback=model.feedback,
        created_at=model.created_at,
    )


class SQLAlchemyJournalAnalysisRepository(JournalAnalysisRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        journal_id: int,
        productivity_score: float,
        sentiment_score: float,
        goal_alignment_score: float,
        risk_level: str,
        feedback: str,
    ) -> JournalAnalysis:
        model = JournalAnalysisModel(
            journal_id=journal_id,
            productivity_score=productivity_score,
            sentiment_score=sentiment_score,
            goal_alignment_score=goal_alignment_score,
            risk_level=risk_level,
            feedback=feedback,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def get_by_journal_id(self, journal_id: int) -> Optional[JournalAnalysis]:
        result = await self.db.execute(
            select(JournalAnalysisModel).where(JournalAnalysisModel.journal_id == journal_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
