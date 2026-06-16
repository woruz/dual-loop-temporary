"""
LOCATION: app/infrastructure/adapters/user_repository.py

WHY HERE: This is the CONCRETE implementation of UserRepositoryPort.
It knows about SQLAlchemy and Postgres — the use-cases don't.

Pattern: maps between DB model (UserModel) ↔ domain entity (User).
This translation layer is called an "anti-corruption layer."
"""

from datetime import datetime
from typing import Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.entities.user import GithubProfile, OAuthToken, User
from app.core.ports.auth_ports import UserRepositoryPort
from app.infrastructure.adapters.database import Usermodel


def _model_to_entity(model: Usermodel) -> User:
    return User(
        id=model.id,
        github_id=model.github_id,
        github_username=model.username,
        email=model.email,
        github_url=model.github_url,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyUserRepository(UserRepositoryPort):
    """
    Postgres implementation of UserRepositoryPort using async SQLAlchemy.
    Injected into use-cases via dependencies.py.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(Usermodel).where(Usermodel.id == user_id))
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_github_id(self, github_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(Usermodel).where(Usermodel.github_id == github_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_by_github_username(self, github_username: str) -> Optional[User]:
        result = await self.db.execute(
            select(Usermodel).where(Usermodel.username == github_username)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def create_from_github_profile(
        self, profile: GithubProfile, token: OAuthToken
    ) -> User:
        model = Usermodel(
            github_id=profile.github_id,
            username=profile.login,
            email=profile.email or f"{profile.login}@users.noreply.github.com",
            github_url=f"https://github.com/{profile.login}",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def create(
        self, profile: GithubProfile, access_token: Union[str, OAuthToken]
    ) -> User:
        """Backward-compatible helper used by auth use case."""
        if isinstance(access_token, str):
            token = OAuthToken(
                access_token=access_token,
                refresh_token="",
                token_type="bearer",
            )
        else:
            token = access_token
        return await self.create_from_github_profile(profile, token)

    async def update(self, user: User) -> User:
        result = await self.db.execute(select(Usermodel).where(Usermodel.id == user.id))
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"User {user.id} not found for update")

        model.username = user.github_username
        model.email = user.email
        model.github_url = user.github_url
        model.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(model)
        return _model_to_entity(model)

    async def update_access_token(self, user_id: int, token: OAuthToken) -> None:
        result = await self.db.execute(select(Usermodel).where(Usermodel.id == user_id))
        model = result.scalar_one_or_none()
        if model:
            model.updated_at = datetime.utcnow()
            await self.db.flush()
