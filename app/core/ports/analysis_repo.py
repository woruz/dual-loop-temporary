from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from app.core.entities.analysis import Analysis

class AnalysisRepositoryPort(ABC):
    @abstractmethod
    async def create(self, analysis: Analysis) -> Analysis:
        """Persists a new Analysis entry in the database."""
        pass

    @abstractmethod
    async def get_by_journal_id(self, journal_id: UUID) -> Optional[Analysis]:
        """Retrieves the analysis associated with a specific journal entry."""
        pass
