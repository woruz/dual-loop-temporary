from typing import Protocol
from uuid import UUID
from app.core.entities.auth import User, OAuthProfile

class IAuthRepo(Protocol):
    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve a user by their email address."""
        ...

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by their unique database ID."""
        ...

    async def create_user(self, user: User) -> User:
        """Create and persist a new user."""
        ...

    async def get_oauth_profile(self, provider: str, provider_user_id: str) -> OAuthProfile | None:
        """Retrieve an OAuth profile by provider and its user ID."""
        ...

    async def create_oauth_profile(self, profile: OAuthProfile) -> OAuthProfile:
        """Create and persist an OAuth profile linked to a user."""
        ...
