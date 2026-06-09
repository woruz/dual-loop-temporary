from abc import ABC, abstractmethod
from uuid import UUID
from app.core.entities.auth import User, OAuthProfile 

class AuthRepo(ABC):

    @abstractmethod
    async def get_user_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    async def create_user(self, user: User) -> User: ...

    @abstractmethod
    async def get_oauth_profile(
        self, provider: str, provider_user_id: str
    ) -> OAuthProfile | None: ...

    @abstractmethod
    async def create_oauth_profile(self, profile: OAuthProfile) -> OAuthProfile: ...