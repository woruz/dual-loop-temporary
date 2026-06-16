from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class GitHubUserInfo:
    provider_user_id: str   # GitHub's numeric ID as string
    email: str
    username: str           # @handle
    avatar_url: str | None

class OAuthPort(ABC):
    @abstractmethod
    async def exchange_code(self, code: str) -> GitHubUserInfo: ...
    
    @abstractmethod
    def get_authorization_url(self, state: str) -> str: ...