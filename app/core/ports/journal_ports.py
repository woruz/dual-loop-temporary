from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.core.entities.goal import Goal
from app.core.entities.journal import Journal
from app.core.entities.journal_analysis import JournalAnalysis


@dataclass
class JournalAnalysisResult:
    productivity_score: float
    sentiment_score: float
    goal_alignment_score: float
    risk_level: str
    feedback: str


class GoalRepositoryPort(ABC):
    @abstractmethod
    async def create(self, user_id: int, goal_name: str, description: str) -> Goal:
        ...

    @abstractmethod
    async def get_by_id(self, goal_id: int) -> Optional[Goal]:
        ...

    @abstractmethod
    async def get_by_id_and_user(self, goal_id: int, user_id: int) -> Optional[Goal]:
        ...


class JournalRepositoryPort(ABC):
    @abstractmethod
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
        ...

    @abstractmethod
    async def get_by_id(self, journal_id: int) -> Optional[Journal]:
        ...

    @abstractmethod
    async def get_by_id_and_user(self, journal_id: int, user_id: int) -> Optional[Journal]:
        ...


class JournalAnalysisRepositoryPort(ABC):
    @abstractmethod
    async def create(
        self,
        journal_id: int,
        productivity_score: float,
        sentiment_score: float,
        goal_alignment_score: float,
        risk_level: str,
        feedback: str,
    ) -> JournalAnalysis:
        ...

    @abstractmethod
    async def get_by_journal_id(self, journal_id: int) -> Optional[JournalAnalysis]:
        ...


class JournalLLMPort(ABC):
    @abstractmethod
    async def analyze_journal(
        self,
        goal: Goal,
        journal: Journal,
    ) -> JournalAnalysisResult:
        ...
