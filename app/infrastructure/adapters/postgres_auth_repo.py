import logging
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.entities.auth import User, OAuthProfile
from app.core.ports.auth_repo import AuthRepo

logger = logging.getLogger("app.infrastructure.adapters.postgres_auth_repo")

class PostgresAuthRepo(AuthRepo):
    def __init__(self, session: AsyncSession):
        self.db = session
        logger.debug("PostgresAuthRepo initialized with DB session")

    async def get_user_by_email(self, email: str) -> User | None:
        logger.info(f"Database query: get_user_by_email for email='{email}'")
        try:
            row = (await self.db.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": email},
            )).mappings().first()
            
            if row:
                logger.debug(f"User found for email '{email}': id='{row['id']}'")
                return self._row_to_user(row)
            else:
                logger.debug(f"No user found for email '{email}'")
                return None
        except Exception as e:
            logger.error(f"Error querying user by email '{email}': {e}", exc_info=True)
            raise

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        logger.info(f"Database query: get_user_by_id for id='{user_id}'")
        try:
            row = (await self.db.execute(
                text("SELECT * FROM users WHERE id = :id"),
                {"id": str(user_id)},
            )).mappings().first()
            
            if row:
                logger.debug(f"User found for id '{user_id}'")
                return self._row_to_user(row)
            else:
                logger.debug(f"No user found for id '{user_id}'")
                return None
        except Exception as e:
            logger.error(f"Error querying user by ID '{user_id}': {e}", exc_info=True)
            raise

    async def create_user(self, user: User) -> User:
        logger.info(f"Database insert: create_user with email='{user.email}' id='{user.id}'")
        try:
            await self.db.execute(
                text("""
                    INSERT INTO users (id, email, hashed_password, is_verified, created_at)
                    VALUES (:id, :email, :hashed_password, :is_verified, :created_at)
                """),
                {
                    "id": str(user.id),
                    "email": user.email,
                    "hashed_password": user.hashed_password,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at,
                },
            )
            await self.db.commit()
            logger.debug(f"User successfully created with email='{user.email}'")
            return user
        except Exception as e:
            logger.error(f"Error creating user with email '{user.email}': {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def get_oauth_profile(
        self, provider: str, provider_user_id: str
    ) -> OAuthProfile | None:
        logger.info(f"Database query: get_oauth_profile for provider='{provider}' and provider_user_id='{provider_user_id}'")
        try:
            row = (await self.db.execute(
                text("""
                    SELECT * FROM oauth_profiles
                    WHERE provider = :provider AND provider_user_id = :pid
                """),
                {"provider": provider, "pid": provider_user_id},
            )).mappings().first()
            
            if row:
                logger.debug(f"OAuth profile found for provider '{provider}' and id '{provider_user_id}'")
                return self._row_to_profile(row)
            else:
                logger.debug(f"No OAuth profile found for provider '{provider}' and id '{provider_user_id}'")
                return None
        except Exception as e:
            logger.error(f"Error querying OAuth profile: {e}", exc_info=True)
            raise

    async def create_oauth_profile(self, profile: OAuthProfile) -> OAuthProfile:
        logger.info(f"Database insert: create_oauth_profile for provider='{profile.provider}' provider_user_id='{profile.provider_user_id}'")
        try:
            await self.db.execute(
                text("""
                    INSERT INTO oauth_profiles
                        (id, user_id, provider, provider_user_id, username, avatar_url)
                    VALUES
                        (:id, :user_id, :provider, :provider_user_id, :username, :avatar_url)
                """),
                {
                    "id": str(profile.id),
                    "user_id": str(profile.user_id),
                    "provider": profile.provider,
                    "provider_user_id": profile.provider_user_id,
                    "username": profile.username,
                    "avatar_url": profile.avatar_url,
                },
            )
            await self.db.commit()
            logger.debug("OAuth profile successfully created")
            return profile
        except Exception as e:
            logger.error(f"Error creating OAuth profile for user_id '{profile.user_id}': {e}", exc_info=True)
            await self.db.rollback()
            raise

    @staticmethod
    def _row_to_user(row) -> User:
        user_id = row["id"]
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return User(
            id=user_id,
            email=row["email"],
            hashed_password=row["hashed_password"],
            is_verified=row["is_verified"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_profile(row) -> OAuthProfile:
        profile_id = row["id"]
        if isinstance(profile_id, str):
            profile_id = UUID(profile_id)
        user_id = row["user_id"]
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return OAuthProfile(
            id=profile_id,
            user_id=user_id,
            provider=row["provider"],
            provider_user_id=row["provider_user_id"],
            username=row["username"],
            avatar_url=row["avatar_url"],
        )