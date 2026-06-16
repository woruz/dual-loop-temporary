from abc import ABC, abstractmethod
from uuid import UUID
from app.core.entities.webhook import Repo, Commit

class WebhookRepo(ABC):
    """
    Operations for storing and querying Webhook metadata.
    """
    @abstractmethod
    async def get_user_id_by_github_username(self, username: str) -> UUID | None:
        """
        Resolves a system user_id UUID from a GitHub username via the oauth_profiles table.
        """
        ...

    @abstractmethod
    async def get_repo_by_name(self, name: str) -> Repo | None:
        """
        Finds a repo by its full name.
        """
        ...

    @abstractmethod
    async def create_repo(self, repo: Repo) -> Repo:
        """
        create new repository.
        """
        ...

    @abstractmethod
    async def create_commit(self, commit: Commit) -> Commit:
        """
        Saving the commit in the DB.
        """
        ...
