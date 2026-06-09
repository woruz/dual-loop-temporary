import logging
from app.core.entities.auth import User, OAuthProfile
from app.core.ports.auth_repo import AuthRepo
from app.core.ports.oauth_port import OAuthPort

logger = logging.getLogger("app.core.use_cases.github_oauth_login")

class GitHubOAuthLogin:
    def __init__(self, repo: AuthRepo, github: OAuthPort):
        self.repo = repo
        self.github = github

    async def execute(self, code: str) -> User:
        logger.info("Execution started: GitHubOAuthLogin flow")
        
        try:
            info = await self.github.exchange_code(code)
        except Exception as e:
            logger.error(f"GitHub code exchange failed: {e}", exc_info=True)
            raise ValueError(f"GitHub authentication failed: {e}")

        logger.info(f"Received GitHub user info: email='{info.email}' login='{info.username}' provider_user_id='{info.provider_user_id}'")

        # 1. Already linked → just return the user
        profile = await self.repo.get_oauth_profile("github", info.provider_user_id)
        if profile:
            logger.info(f"OAuth profile already exists. Logging in linked user: id='{profile.user_id}'")
            user = await self.repo.get_user_by_id(profile.user_id)
            if not user:
                logger.error(f"Linked user not found: id='{profile.user_id}'")
                raise ValueError("Linked user not found")
            return user

        # 2. Email exists but no OAuth link → link it
        user = await self.repo.get_user_by_email(info.email)
        if not user:
            # 3. Brand new user — create account
            logger.info(f"No user found with email '{info.email}'. Creating new user account.")
            user = await self.repo.create_user(User(
                email=info.email,
                hashed_password=None,   # OAuth-only, no password
                is_verified=True,       # GitHub already verified the email
            ))
            logger.info(f"New user account created: id='{user.id}' email='{user.email}'")
        else:
            logger.info(f"Found existing user with email '{info.email}'. Linking GitHub profile.")

        # Create the OAuth Profile link
        new_profile = OAuthProfile(
            user_id=user.id,
            provider="github",
            provider_user_id=info.provider_user_id,
            username=info.username,
            avatar_url=info.avatar_url,
        )
        await self.repo.create_oauth_profile(new_profile)
        logger.info(f"Successfully linked GitHub profile '{info.username}' with user id='{user.id}'")
        
        logger.info("Execution complete: GitHubOAuthLogin successful")
        return user