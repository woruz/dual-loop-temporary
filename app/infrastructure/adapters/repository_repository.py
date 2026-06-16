from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.repository import Repository
from app.core.ports.repository_ports import RepositoryRepositoryPort
from app.infrastructure.adapters.repository_models import RepositoryModel


def _model_to_entity(model: RepositoryModel) -> Repository:
    return Repository(
        id=model.id,
        user_id=model.user_id,
        repo_name=model.repo_name,
        repo_url=model.repo_url,
        created_at=model.created_at,
    )


class SQLAlchemyRepositoryRepository(RepositoryRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, repo_name: str, repo_url: str) -> Repository:
        model = RepositoryModel(
            user_id=user_id,
            repo_name=repo_name,
            repo_url=repo_url,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def get_by_id(self, repository_id: int) -> Optional[Repository]:
        result = await self.db.execute(
            select(RepositoryModel).where(RepositoryModel.id == repository_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_id_and_user(
        self, repository_id: int, user_id: int
    ) -> Optional[Repository]:
        result = await self.db.execute(
            select(RepositoryModel).where(
                RepositoryModel.id == repository_id,
                RepositoryModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def list_by_user(self, user_id: int) -> list[Repository]:
        result = await self.db.execute(
            select(RepositoryModel)
            .where(RepositoryModel.user_id == user_id)
            .order_by(RepositoryModel.created_at.desc())
        )
        models = result.scalars().all()
        return [_model_to_entity(model) for model in models]
