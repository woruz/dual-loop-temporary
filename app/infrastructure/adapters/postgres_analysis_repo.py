import logging
from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.entities.analysis import Analysis
from app.core.ports.analysis_repo import AnalysisRepositoryPort

logger = logging.getLogger("app.infrastructure.adapters.postgres_analysis_repo")

class PostgresAnalysisRepo(AnalysisRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create(self, analysis: Analysis) -> Analysis:
        logger.info(f"Database insert: create analysis for journal_id='{analysis.journal_id}'")
        try:
            await self.db.execute(
                text("""
                    INSERT INTO analyses (
                        id, journal_id, productivity_score, sentiment_score, goal_alignment_score, 
                        risk_level, missing_goal, match_goal, recommendation, created_at
                    )
                    VALUES (
                        :id, :journal_id, :productivity_score, :sentiment_score, :goal_alignment_score, 
                        :risk_level, :missing_goal, :match_goal, :recommendation, :created_at
                    )
                """),
                {
                    "id": str(analysis.id),
                    "journal_id": str(analysis.journal_id),
                    "productivity_score": analysis.productivity_score,
                    "sentiment_score": analysis.sentiment_score,
                    "goal_alignment_score": analysis.goal_alignment_score,
                    "risk_level": analysis.risk_level,
                    "missing_goal": analysis.missing_goal,
                    "match_goal": analysis.match_goal,
                    "recommendation": analysis.recommendation,
                    "created_at": analysis.created_at
                }
            )
            await self.db.commit()
            logger.debug(f"Analysis created successfully with id='{analysis.id}'")
            return analysis
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating analysis: {e}", exc_info=True)
            raise

    async def get_by_journal_id(self, journal_id: UUID) -> Optional[Analysis]:
        logger.info(f"Database query: get analysis by journal_id='{journal_id}'")
        try:
            row = (await self.db.execute(
                text("SELECT * FROM analyses WHERE journal_id = :journal_id"),
                {"journal_id": str(journal_id)}
            )).mappings().first()
            if row:
                return self._row_to_analysis(row)
            return None
        except Exception as e:
            logger.error(f"Error fetching analysis by journal_id '{journal_id}': {e}", exc_info=True)
            raise

    @staticmethod
    def _row_to_analysis(row) -> Analysis:
        return Analysis(
            id=UUID(row["id"]),
            journal_id=UUID(row["journal_id"]),
            productivity_score=row["productivity_score"],
            sentiment_score=row["sentiment_score"],
            goal_alignment_score=row["goal_alignment_score"],
            risk_level=row["risk_level"],
            missing_goal=row["missing_goal"],
            match_goal=row["match_goal"],
            recommendation=row["recommendation"],
            created_at=row["created_at"]
        )
