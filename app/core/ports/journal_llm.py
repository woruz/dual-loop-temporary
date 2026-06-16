from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from app.core.entities.journal import Journal

@dataclass
class JournalAnalysisResult:
    productivity_score: float
    sentiment_score: float
    goal_alignment_score: float
    risk_level: str
    missing_goal: str
    match_goal: str
    recommendation: str

class JournalLLMPort(ABC):
    @abstractmethod
    async def analyze_journal(
        self,
        user_goal: str,
        user_experience: str,
        journal: Journal,
        commits: list[dict]
    ) -> JournalAnalysisResult:
        """
        Sends the journal text, user goals/experience, and daily commits list
        to the LLM for structured productivity analysis and feedback.
        """
        pass
