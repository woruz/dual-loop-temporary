import logging
from uuid import UUID
from app.core.entities.auth import User
from app.core.ports.auth_repo import AuthRepo

logger = logging.getLogger("app.core.use_cases.verify_journal")

class VerifyJournal:
    def __init__(self, repo: AuthRepo):
        self.repo = repo

    async def execute(self, user_id: UUID, full_name: str, goal: str, experience: str) -> User:
        logger.info(f"Execution started: VerifyJournal for user_id='{user_id}'")
        
        # Validate inputs
        if not full_name or not full_name.strip():
            raise ValueError("Full name is required")
        if not goal or not goal.strip():
            raise ValueError("Goal is required")
        if not experience or not experience.strip():
            raise ValueError("Experience is required")
            
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            logger.warning(f"Verification failed: User '{user_id}' not found")
            raise ValueError("User not found")
            
        user.full_name = full_name.strip()
        user.goal = goal.strip()
        user.experience = experience.strip()
        user.is_verified_forjournal = True
        
        updated_user = await self.repo.update_user(user)
        logger.info(f"Execution complete: User successfully verified for journal email='{user.email}' id='{user.id}'")
        return updated_user
