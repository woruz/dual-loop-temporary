import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID
from app.core.entities.webhook import Repo, Commit
from app.core.ports.webhook_repo import WebhookRepo

logger = logging.getLogger("app.core.use_cases.process_webhook")

class ProcessWebhookUseCase:
    """
    Use Case that orchestrates Webhook processing:
    1. Extracts commit messages and structural repository/author details.
    2. Persists payload JSON using a PayloadStorage adapter.
    3. Identifies matching users in our database via their GitHub OAuth username.
    4. Persists Repository and Commit entities in the database.
    """
    def __init__(self, repo: WebhookRepo):
        self.repo = repo

    async def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        System parses the incoming commits and stores the data in the database first
        """
        logger.info("Executing ProcessWebhookUseCase...")

        repo_data = payload.get("repository", {})
        repo_name = repo_data.get("full_name", "")

        if not repo_name:
            logger.error("Failed to process webhook: Missing repository name in payload.")
            raise ValueError("Invalid payload: missing repository name")

        ref = payload.get("ref", "")
        branch = ref.split("/")[-1] if ref else "unknown_branch"

        # 1. Parse incoming commits
        incoming_commits = payload.get("commits", [])
        commit_messages_map = {}

        for item in incoming_commits:
            sha = item.get("id") or item.get("commit_sha") or "unknown_sha"
            message = item.get("message") or "No message"
            commit_messages_map[sha] = message

        # 2. Resolve Owner User (checks if registered in our system via oauth_profiles)
        owner_username = "unknown_owner"
        if "/" in repo_name:
            owner_username = repo_name.split("/")[0]
        else:
            owner_username = repo_data.get("owner", {}).get("login") or "unknown_owner"

        owner_user_id = await self.repo.get_user_id_by_github_username(owner_username)

        # 4. Resolve/Create Repo Entity
        db_repo = await self.repo.get_repo_by_name(repo_name)
        if not db_repo:
            logger.info(f"Repository '{repo_name}' not found. Creating new repo entity...")
            new_repo = Repo(
                name=repo_name,
                owner_username=owner_username,
                user_id=owner_user_id
            )
            db_repo = await self.repo.create_repo(new_repo)

        # 5. Resolve Pusher User (checks if registered in our system via oauth_profiles)
        sender_username = payload.get("sender", {}).get("login")
        if not sender_username:
            if incoming_commits:
                author_data = incoming_commits[0].get("author", {})
                sender_username = author_data.get("username") or author_data.get("name") or owner_username
            else:
                sender_username = owner_username

        pusher_user_id = await self.repo.get_user_id_by_github_username(sender_username)

        # 6. Parse push timestamp
        push_timestamp = datetime.utcnow()
        if incoming_commits:
            ts_str = incoming_commits[0].get("timestamp")
            if ts_str:
                try:
                    # Convert ISO to native datetime in UTC
                    push_timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    logger.warning(f"Failed to parse commit timestamp '{ts_str}', defaulting to UTC now.")

        # 7. Create Commit Entity
        new_commit = Commit(
            repo_id=db_repo.id,
            user_id=pusher_user_id,
            branch=branch,
            message=commit_messages_map,
            total_commit=len(incoming_commits),
            pusher_username=sender_username,
            timestamp=push_timestamp
        )
        await self.repo.create_commit(new_commit)

        result = {
            "status": "success",
            "message": f"Successfully processed {len(incoming_commits)} commits.",
            "repository": repo_name,
            "branch": branch
        }
        return result
