"""Shared authentication and OAuth configuration."""

import logging
import os
from datetime import datetime

from app.core.entities.user import User

logger = logging.getLogger(__name__)

DEFAULT_GITHUB_REDIRECT_URI = "http://127.0.0.1:8000/auth/github/callback"


def get_environment() -> str:
    return os.getenv("ENVIRONMENT", "development").strip().lower()


def is_development() -> bool:
    return get_environment() == "development"


def get_github_redirect_uri() -> str:
    """Return normalized GitHub OAuth callback URL."""
    uri = os.getenv("GITHUB_REDIRECT_URI", DEFAULT_GITHUB_REDIRECT_URI).strip()
    if uri.endswith("/"):
        uri = uri.rstrip("/")
    return uri


def get_dev_user() -> User:
    """Mock user for local development and Swagger testing."""
    return User(
        id=1,
        github_id=123,
        github_username="dev_user",
        email="dev@test.com",
        github_url="https://github.com/dev_user",
        is_active=True,
        name="Development User",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def log_oauth_startup_config() -> None:
    redirect_uri = get_github_redirect_uri()
    environment = get_environment()
    client_id = os.getenv("GITHUB_CLIENT_ID", "")

    logger.info("ENVIRONMENT=%s", environment)
    logger.info("GITHUB_REDIRECT_URI=%s", redirect_uri)
    logger.info(
        "GitHub OAuth client_id=%s",
        f"{client_id[:6]}..." if len(client_id) > 6 else "(not set)",
    )
    if is_development():
        logger.warning(
            "Development auth bypass ENABLED — protected routes use mock user id=1 "
            "without JWT. Set ENVIRONMENT=production to require real authentication."
        )
    if "localhost" in redirect_uri:
        logger.warning(
            "GITHUB_REDIRECT_URI uses 'localhost'. GitHub OAuth Apps must register "
            "the EXACT callback URL. If your app uses 127.0.0.1, update GitHub settings "
            "or set GITHUB_REDIRECT_URI=http://127.0.0.1:8000/auth/github/callback"
        )
