from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.core.entities.journal import Journal

class JournalRepositoryPort(ABC):
    @abstractmethod
    async def create(self, journal: Journal) -> Journal:
        """Persists a new Journal entry in the database."""
        pass

    @abstractmethod
    async def get_by_id(self, journal_id: UUID) -> Optional[Journal]:
        """Retrieves a Journal by its unique ID."""
        pass

    @abstractmethod
    async def get_by_user_and_date(self, user_id: UUID, date: datetime) -> Optional[Journal]:
        """Retrieves a user's journal entry for a specific calendar date."""
        pass

    @abstractmethod
    async def get_commits_by_user_and_date(self, user_id: UUID, date: datetime) -> list[dict]:
        """Retrieves all commits and their repository names for a user on a given date."""
        pass
