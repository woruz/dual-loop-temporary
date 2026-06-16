from app.core.entities.journal_analysis import JournalAnalysis
from app.core.ports.journal_ports import (
    GoalRepositoryPort,
    JournalAnalysisRepositoryPort,
    JournalLLMPort,
    JournalRepositoryPort,
)


class AnalyzeJournalUseCase:
    def __init__(
        self,
        journal_repo: JournalRepositoryPort,
        goal_repo: GoalRepositoryPort,
        analysis_repo: JournalAnalysisRepositoryPort,
        llm: JournalLLMPort,
    ):
        self.journal_repo = journal_repo
        self.goal_repo = goal_repo
        self.analysis_repo = analysis_repo
        self.llm = llm

    async def execute(self, user_id: int, journal_id: int) -> JournalAnalysis:
        journal = await self.journal_repo.get_by_id_and_user(journal_id, user_id)
        if not journal:
            raise ValueError(f"Journal {journal_id} not found for user {user_id}")

        goal = await self.goal_repo.get_by_id_and_user(journal.goal_id, user_id)
        if not goal:
            raise ValueError(f"Goal {journal.goal_id} not found for user {user_id}")

        existing = await self.analysis_repo.get_by_journal_id(journal_id)
        if existing:
            return existing

        result = await self.llm.analyze_journal(goal=goal, journal=journal)

        return await self.analysis_repo.create(
            journal_id=journal_id,
            productivity_score=result.productivity_score,
            sentiment_score=result.sentiment_score,
            goal_alignment_score=result.goal_alignment_score,
            risk_level=result.risk_level,
            feedback=result.feedback,
        )
