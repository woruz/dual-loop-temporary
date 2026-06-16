from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.journal import Journal
from app.core.ports.journal_ports import JournalRepositoryPort
from app.infrastructure.adapters.journal_models import JournalModel


def _model_to_entity(model: JournalModel) -> Journal:
    return Journal(
        id=model.id,
        user_id=model.user_id,
        goal_id=model.goal_id,
        study_hours=model.study_hours,
        today_work=model.today_work,
        learning_notes=model.learning_notes,
        challenges=model.challenges,
        tomorrow_plan=model.tomorrow_plan,
        created_at=model.created_at,
    )


class SQLAlchemyJournalRepository(JournalRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        goal_id: int,
        study_hours: float,
        today_work: str,
        learning_notes: str,
        challenges: str,
        tomorrow_plan: str,
    ) -> Journal:
        model = JournalModel(
            user_id=user_id,
            goal_id=goal_id,
            study_hours=study_hours,
            today_work=today_work,
            learning_notes=learning_notes,
            challenges=challenges,
            tomorrow_plan=tomorrow_plan,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def get_by_id(self, journal_id: int) -> Optional[Journal]:
        result = await self.db.execute(
            select(JournalModel).where(JournalModel.id == journal_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_id_and_user(self, journal_id: int, user_id: int) -> Optional[Journal]:
        result = await self.db.execute(
            select(JournalModel).where(
                JournalModel.id == journal_id,
                JournalModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
