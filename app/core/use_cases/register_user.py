import logging
from app.core.entities.auth import User
from app.core.ports.auth_repo import AuthRepo
from app.core.ports.password_hasher import IPasswordHasher

logger = logging.getLogger("app.core.use_cases.register_user")

class RegisterUser:
    def __init__(self, repo: AuthRepo, hasher: IPasswordHasher):
        self.repo = repo
        self.hasher = hasher

    async def execute(self, email: str, password: str) -> User:
        logger.info(f"Execution started: RegisterUser for email='{email}'")
        
        existing_user = await self.repo.get_user_by_email(email)
        if existing_user:
            logger.warning(f"Registration failed: Email already registered '{email}'")
            raise ValueError("Email already registered")

        hashed_password = self.hasher.hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_verified=False,
        )
        
        created_user = await self.repo.create_user(user)
        logger.info(f"Execution complete: User successfully registered email='{email}' id='{created_user.id}'")
        return created_user