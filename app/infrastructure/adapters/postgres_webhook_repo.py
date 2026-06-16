import json
import logging
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.entities.webhook import Repo, Commit
from app.core.ports.webhook_repo import WebhookRepo

logger = logging.getLogger("app.infrastructure.adapters.postgres_webhook_repo")

class PostgresWebhookRepo(WebhookRepo):
    """
    Adapter implementing the WebhookRepo port using PostgreSQL raw async SQL statements.
    Works seamlessly with SQLite fallback as well.
    """
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_id_by_github_username(self, username: str) -> UUID | None:
        logger.info(f"Database query: get_user_id_by_github_username for username='{username}'")
        try:
            row = (await self.db.execute(
                text("""
                    SELECT user_id FROM oauth_profiles
                    WHERE provider = 'github' AND username = :username
                """),
                {"username": username}
            )).mappings().first()
            if row and row["user_id"]:
                return UUID(row["user_id"])
            return None
        except Exception as e:
            logger.error(f"Error querying user_id by github username '{username}': {e}", exc_info=True)
            raise

    async def get_repo_by_name(self, name: str) -> Repo | None:
        logger.info(f"Database query: get_repo_by_name for name='{name}'")
        try:
            row = (await self.db.execute(
                text("""
                    SELECT * FROM repos WHERE name = :name
                """),
                {"name": name}
            )).mappings().first()
            if row:
                return Repo(
                    id=UUID(row["id"]),
                    name=row["name"],
                    owner_username=row["owner_username"],
                    user_id=UUID(row["user_id"]) if row["user_id"] else None,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            return None
        except Exception as e:
            logger.error(f"Error querying repo by name '{name}': {e}", exc_info=True)
            raise

    async def create_repo(self, repo: Repo) -> Repo:
        logger.info(f"Database insert: create_repo with name='{repo.name}' id='{repo.id}'")
        try:
            await self.db.execute(
                text("""
                    INSERT INTO repos (id, name, owner_username, user_id, created_at, updated_at)
                    VALUES (:id, :name, :owner_username, :user_id, :created_at, :updated_at)
                """),
                {
                    "id": str(repo.id),
                    "name": repo.name,
                    "owner_username": repo.owner_username,
                    "user_id": str(repo.user_id) if repo.user_id else None,
                    "created_at": repo.created_at,
                    "updated_at": repo.updated_at
                }
            )
            await self.db.commit()
            return repo
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating repo '{repo.name}': {e}", exc_info=True)
            raise

    async def create_commit(self, commit: Commit) -> Commit:
        logger.info(f"Database insert: create_commit for repo_id='{commit.repo_id}' branch='{commit.branch}'")
        try:
            # Serialize the commit messages dictionary to JSON
            message_json = json.dumps(commit.message)
            await self.db.execute(
                text("""
                    INSERT INTO commits (id, repo_id, user_id, pusher_username, branch, message, total_commit, timestamp)
                    VALUES (:id, :repo_id, :user_id, :pusher_username, :branch, :message, :total_commit, :timestamp)
                """),
                {
                    "id": str(commit.id),
                    "repo_id": str(commit.repo_id),
                    "user_id": str(commit.user_id) if commit.user_id else None,
                    "pusher_username": commit.pusher_username,
                    "branch": commit.branch,
                    "message": message_json,
                    "total_commit": commit.total_commit,
                    "timestamp": commit.timestamp
                }
            )
            await self.db.commit()
            return commit
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating commit entry: {e}", exc_info=True)
            raise
