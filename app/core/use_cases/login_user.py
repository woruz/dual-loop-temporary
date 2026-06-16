import logging
from app.core.entities.auth import User
from app.core.ports.auth_repo import AuthRepo
from app.core.ports.password_hasher import IPasswordHasher

logger = logging.getLogger("app.core.use_cases.login_user")

class LoginUser:
    def __init__(self, repo: AuthRepo, hasher: IPasswordHasher):
        self.repo = repo
        self.hasher = hasher

    async def execute(self, email: str, password: str) -> User:
        logger.info(f"Execution started: LoginUser for email='{email}'")
        
        user = await self.repo.get_user_by_email(email)
        
        # Prevent email enumeration attacks by keeping warning/error messages identical
        if not user:
            logger.warning(f"Login failed: No user found for email='{email}'")
            raise ValueError("Invalid credentials")
            
        if not user.hashed_password:
            logger.warning(f"Login failed: User '{email}' exists but has no password (registered via OAuth only)")
            raise ValueError("This account was created via GitHub. Please log in using 'Continue with GitHub' or set a password in your profile.")

        if not self.hasher.verify(password, user.hashed_password):
            logger.warning(f"Login failed: Incorrect password for email='{email}'")
            raise ValueError("Invalid credentials")

        logger.info(f"Execution complete: User successfully logged in email='{email}' id='{user.id}'")
        return user