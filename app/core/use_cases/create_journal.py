import logging
from datetime import datetime
from uuid import UUID
from app.core.entities.journal import Journal
from app.core.entities.analysis import Analysis
from app.core.ports.journal_repo import JournalRepositoryPort
from app.core.ports.analysis_repo import AnalysisRepositoryPort
from app.core.ports.journal_llm import JournalLLMPort

logger = logging.getLogger("app.core.use_cases.create_journal")

class CreateJournalUseCase:
    def __init__(
        self,
        journal_repo: JournalRepositoryPort,
        analysis_repo: AnalysisRepositoryPort,
        journal_llm: JournalLLMPort
    ):
        self.journal_repo = journal_repo
        self.analysis_repo = analysis_repo
        self.journal_llm = journal_llm

    async def execute(
        self,
        user_id: UUID,
        study_hours: float,
        today_work: str,
        learning_notes: str,
        challenges: str,
        user_goal: str,
        user_experience: str
    ) -> tuple[Journal, Analysis]:
        logger.info(f"Executing CreateJournalUseCase for user_id='{user_id}'")

        # 1. Enforce business rule: Only one journal entry per calendar day
        now = datetime.utcnow()
        existing = await self.journal_repo.get_by_user_and_date(user_id, now)
        if existing:
            logger.warning(f"Journal already exists for user_id='{user_id}' on date='{now.date()}'")
            raise ValueError("A journal entry has already been submitted for today.")

        # 2. Create and persist Journal entity
        journal = Journal(
            user_id=user_id,
            study_hours=study_hours,
            today_work=today_work,
            learning_notes=learning_notes,
            challenges=challenges,
            created_at=now
        )
        saved_journal = await self.journal_repo.create(journal)

        # 3. Retrieve user's commits on the same day
        commits = await self.journal_repo.get_commits_by_user_and_date(user_id, now)

        # 4. Invoke LLM (Groq) for analysis
        analysis_result = await self.journal_llm.analyze_journal(
            user_goal=user_goal,
            user_experience=user_experience,
            journal=saved_journal,
            commits=commits
        )

        # 5. Create and persist Analysis entity
        analysis = Analysis(
            journal_id=saved_journal.id,
            productivity_score=analysis_result.productivity_score,
            sentiment_score=analysis_result.sentiment_score,
            goal_alignment_score=analysis_result.goal_alignment_score,
            risk_level=analysis_result.risk_level,
            missing_goal=analysis_result.missing_goal,
            match_goal=analysis_result.match_goal,
            recommendation=analysis_result.recommendation,
            created_at=now
        )
        saved_analysis = await self.analysis_repo.create(analysis)

        logger.info(f"CreateJournalUseCase execution complete. Journal ID: '{saved_journal.id}', Analysis ID: '{saved_analysis.id}'")
        return saved_journal, saved_analysis
