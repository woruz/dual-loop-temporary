from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.goal import Goal
from app.core.ports.journal_ports import GoalRepositoryPort
from app.infrastructure.adapters.journal_models import GoalModel


def _model_to_entity(model: GoalModel) -> Goal:
    return Goal(
        id=model.id,
        user_id=model.user_id,
        goal_name=model.goal_name,
        description=model.description,
    )


class SQLAlchemyGoalRepository(GoalRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, goal_name: str, description: str) -> Goal:
        model = GoalModel(
            user_id=user_id,
            goal_name=goal_name,
            description=description,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def get_by_id(self, goal_id: int) -> Optional[Goal]:
        result = await self.db.execute(select(GoalModel).where(GoalModel.id == goal_id))
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_id_and_user(self, goal_id: int, user_id: int) -> Optional[Goal]:
        result = await self.db.execute(
            select(GoalModel).where(GoalModel.id == goal_id, GoalModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None
