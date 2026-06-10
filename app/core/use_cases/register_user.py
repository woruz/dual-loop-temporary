import logging

from app.core.entities.auth import User
from app.core.ports.auth_repo import IAuthRepo
from app.core.ports.password_hasher import IPasswordHasher

logger = logging.getLogger(__name__)

class RegisterUserUseCase:
    def __init__(self, auth_repo: IAuthRepo, password_hasher: IPasswordHasher):
        self.auth_repo = auth_repo
        self.password_hasher = password_hasher

    async def execute(self, email: str, password: str) -> User:
        logger.info("Registering user with email: %s", email)

        existing_user_check = await self.auth_repo.get_user_by_email(email)

        if existing_user_check:
            raise ValueError(f"User with email {email} already exists")
        
        
        hashed_password = self.password_hasher.hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            is_verified=False
        )

        created_user = await self.auth_repo.create_user(user)
        logger.info("User registered successfully: %s", created_user.id)

        return created_user
    