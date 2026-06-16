"""
LOCATION: app/core/use_cases/auth_use_cases.py

WHY HERE: Use-cases contain your BUSINESS LOGIC — the "what does our app do?"
They orchestrate entities and ports but know NOTHING about HTTP, databases, or GitHub.

This is the most important layer. It's 100% unit-testable with mock ports.
If GitHub changes their API, only the adapter changes — use-cases stay the same.
"""
import logging
import secrets

from app.core.entities import GithubProfile, OAuthToken, User
from app.core.ports.auth_ports import GithubOAuthPort, TokenServicePort, UserRepositoryPort

logger = logging.getLogger(__name__)


class GithubAuthUseCase:
    """
    Orchestrates the full GitHub OAuth flow:
    1. Generate OAuth URL (with CSRF protection)
    2. Handle callback → exchange code → fetch profile → upsert user → issue JWTs

    Injected via dependency injection (see dependencies.py).
    No imports from infrastructure or server layers — pure business logic.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        oauth_port: GithubOAuthPort,
        token_service: TokenServicePort,
    ):
        self.user_repo = user_repo
        self.oauth_port = oauth_port
        self.token_service = token_service

    def get_ouauth_url(self) -> tuple[str, str]:
        """
        Returns (authorization_url, state).
        The `state` is a CSRF token — store it in the session/cookie,
        verify it matches when GitHub redirects back.
        """
        state = secrets.token_urlsafe(32)
        url = self.oauth_port.get_authorization_url(state)
        logger.info("Generated GitHub OAuth URL with state")
        return url, state

    async def handle_callback(
        self, code: str, state: str, expected_state: str
    ) -> tuple[OAuthToken, User]:
        """
        Full OAuth callback flow. Called when GitHub redirects to /auth/github/callback.

        Returns:
            (OAuthToken, User) — tokens for client, user for logging/response

        Raises:
            ValueError: on CSRF mismatch or GitHub API errors
        """
        if state != expected_state:
            logger.warning("OAuth state mismatch — possible CSRF attack")
            raise ValueError("Invalid OAuth state — please try logging in again")

        logger.info("Exchanging OAuth code for GitHub access token")
        github_access_token = await self.oauth_port.exchange_code_for_token(code)
        logger.info("exchange_code_for_token completed")

        logger.info("Fetching user profile from GitHub")
        profile = await self.oauth_port.get_user_profile(github_access_token)
        logger.info("get_user_profile completed: login=%s", profile.login)

        github_oauth_token = OAuthToken(
            access_token=github_access_token,
            refresh_token="",
            token_type="bearer",
        )

        logger.info("Looking up user by GitHub username: %s", profile.login)
        existing_user = await self.user_repo.get_by_github_username(profile.login)
        logger.info(
            "get_by_github_username completed: found=%s",
            existing_user is not None,
        )

        if existing_user:
            existing_user.github_username = profile.login
            existing_user.email = profile.email or existing_user.email
            user = await self.user_repo.update(existing_user)
            logger.info("update user completed: id=%s, login=%s", user.id, user.github_username)
            await self.user_repo.update_access_token(user.id, github_oauth_token)
            logger.info("update_access_token completed for user id=%s", user.id)
        else:
            user = await self.user_repo.create_from_github_profile(profile, github_oauth_token)
            logger.info("create user completed: id=%s, login=%s", user.id, user.github_username)

        logger.info("Creating access token for user id=%s", user.id)
        access_token = self.token_service.create_access_token(user.id, user.github_username)
        logger.info("create_access_token completed for user id=%s", user.id)
        refresh_token = self.token_service.create_refresh_token(user.id)

        tokens = OAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )
        return tokens, user

    async def refresh_tokens(self, refresh_token: str) -> OAuthToken:
        """Issue new access token using a valid refresh token."""
        payload = self.token_service.verify_refresh_token(refresh_token)
        user_id = int(payload["sub"])

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")

        new_access = self.token_service.create_access_token(user.id, user.github_username)
        new_refresh = self.token_service.create_refresh_token(user.id)

        return OAuthToken(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
        )

    async def get_current_user(self, access_token: str) -> User:
        """Validate JWT and return the user. Used by auth middleware."""
        payload = self.token_service.verify_access_token(access_token)
        user_id = int(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")
        return user
