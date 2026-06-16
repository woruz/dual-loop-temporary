import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.entities.journal import Journal
from app.core.ports.journal_repo import JournalRepositoryPort

logger = logging.getLogger("app.infrastructure.adapters.postgres_journal_repo")

class PostgresJournalRepo(JournalRepositoryPort):
    def __init__(self, session: AsyncSession):
        self.db = session

    async def create(self, journal: Journal) -> Journal:
        logger.info(f"Database insert: create journal for user_id='{journal.user_id}'")
        try:
            await self.db.execute(
                text("""
                    INSERT INTO journals (id, user_id, study_hours, today_work, learning_notes, challenges, created_at)
                    VALUES (:id, :user_id, :study_hours, :today_work, :learning_notes, :challenges, :created_at)
                """),
                {
                    "id": str(journal.id),
                    "user_id": str(journal.user_id),
                    "study_hours": journal.study_hours,
                    "today_work": journal.today_work,
                    "learning_notes": journal.learning_notes,
                    "challenges": journal.challenges,
                    "created_at": journal.created_at
                }
            )
            await self.db.commit()
            logger.debug(f"Journal created successfully with id='{journal.id}'")
            return journal
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating journal: {e}", exc_info=True)
            raise

    async def get_by_id(self, journal_id: UUID) -> Optional[Journal]:
        logger.info(f"Database query: get journal by id='{journal_id}'")
        try:
            row = (await self.db.execute(
                text("SELECT * FROM journals WHERE id = :id"),
                {"id": str(journal_id)}
            )).mappings().first()
            if row:
                return self._row_to_journal(row)
            return None
        except Exception as e:
            logger.error(f"Error fetching journal by id '{journal_id}': {e}", exc_info=True)
            raise

    async def get_by_user_and_date(self, user_id: UUID, date: datetime) -> Optional[Journal]:
        logger.info(f"Database query: get journal for user_id='{user_id}' on date='{date.date()}'")
        try:
            start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59, 999999)
            row = (await self.db.execute(
                text("""
                    SELECT * FROM journals 
                    WHERE user_id = :user_id 
                      AND created_at >= :start_of_day 
                      AND created_at <= :end_of_day
                    LIMIT 1
                """),
                {
                    "user_id": str(user_id),
                    "start_of_day": start_of_day,
                    "end_of_day": end_of_day
                }
            )).mappings().first()
            if row:
                return self._row_to_journal(row)
            return None
        except Exception as e:
            logger.error(f"Error fetching journal by date: {e}", exc_info=True)
            raise

    async def get_commits_by_user_and_date(self, user_id: UUID, date: datetime) -> list[dict]:
        logger.info(f"Database query: get commits for user_id='{user_id}' on date='{date.date()}'")
        try:
            start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59, 999999)
            result = await self.db.execute(
                text("""
                    SELECT c.*, r.name as repo_name 
                    FROM commits c
                    JOIN repos r ON c.repo_id = r.id
                    WHERE c.user_id = :user_id 
                      AND c.timestamp >= :start_of_day 
                      AND c.timestamp <= :end_of_day
                """),
                {
                    "user_id": str(user_id),
                    "start_of_day": start_of_day,
                    "end_of_day": end_of_day
                }
            )
            commits = []
            for row in result.mappings().all():
                msg_raw = row["message"]
                if isinstance(msg_raw, str):
                    try:
                        message = json.loads(msg_raw)
                    except Exception:
                        message = {"raw": msg_raw}
                else:
                    message = msg_raw

                commits.append({
                    "repo_name": row["repo_name"],
                    "branch": row["branch"],
                    "pusher_username": row["pusher_username"],
                    "message": message,
                    "timestamp": row["timestamp"]
                })
            return commits
        except Exception as e:
            logger.error(f"Error fetching commits by date: {e}", exc_info=True)
            raise

    @staticmethod
    def _row_to_journal(row) -> Journal:
        return Journal(
            id=UUID(row["id"]),
            user_id=UUID(row["user_id"]),
            study_hours=row["study_hours"],
            today_work=row["today_work"],
            learning_notes=row["learning_notes"],
            challenges=row["challenges"],
            created_at=row["created_at"]
        )
