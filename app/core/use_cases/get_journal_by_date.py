import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.core.entities.journal import Journal
from app.core.entities.analysis import Analysis
from app.core.ports.journal_repo import JournalRepositoryPort
from app.core.ports.analysis_repo import AnalysisRepositoryPort

logger = logging.getLogger("app.core.use_cases.get_journal_by_date")

class GetJournalByDateUseCase:
    def __init__(
        self,
        journal_repo: JournalRepositoryPort,
        analysis_repo: AnalysisRepositoryPort
    ):
        self.journal_repo = journal_repo
        self.analysis_repo = analysis_repo

    async def execute(self, user_id: UUID, date: datetime) -> Optional[tuple[Journal, Optional[Analysis]]]:
        logger.info(f"Executing GetJournalByDateUseCase for user_id='{user_id}' and date='{date.date()}'")
        
        journal = await self.journal_repo.get_by_user_and_date(user_id, date)
        if not journal:
            logger.info(f"No journal entry found for user_id='{user_id}' on date='{date.date()}'")
            return None

        analysis = await self.analysis_repo.get_by_journal_id(journal.id)
        return journal, analysis
