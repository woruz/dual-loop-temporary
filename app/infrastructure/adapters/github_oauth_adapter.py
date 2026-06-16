"""
LOCATION: app/infrastructure/adapters/github_oauth_adapter.py
 
WHY HERE: This is the CONCRETE implementation of GithubOAuthPort.
All HTTP calls to GitHub live here. httpx for async HTTP.
 
If GitHub changes their API, only THIS file changes.
Use-cases are completely untouched.
"""
import httpx
import logging
import os
from urllib.parse import urlencode

from app.core.entities.user import GithubProfile
from app.core.ports.auth_ports import GithubOAuthPort
from app.server.auth_config import get_github_redirect_uri

logger = logging.getLogger(__name__)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

# Scopes we request from GitHub:
# read:user  → access profile info
# user:email → access primary email (some users hide it, this forces it)
GITHUB_SCOPES = "read:user user:email"
class HttpxGithubOAuthAdapter(GithubOAuthPort):
    """
    Talks to GitHub OAuth & API using httpx async HTTP client.
    Reads credentials from environment variables.
    """
 
    def __init__(self):
        self.client_id = os.getenv("GITHUB_CLIENT_ID", "")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")

        if not self.client_id or not self.client_secret:
            raise RuntimeError(
                "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set"
            )

    @property
    def redirect_uri(self) -> str:
        return get_github_redirect_uri()

    def get_authorization_url(self, state: str) -> str:
        """
        Build the URL to redirect the user to GitHub for login.
        The `state` parameter is a CSRF token.
        """
        params = {
            "client_id": self.client_id,
            "scope": GITHUB_SCOPES,
            "state": state,
            "redirect_uri": self.redirect_uri,
        }
        url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
        logger.info(
            "GitHub OAuth authorize request | redirect_uri=%s | full_url=%s",
            self.redirect_uri,
            url,
        )
        return url

    async def exchange_code_for_token(self, code: str) -> str:
        """
        POST to GitHub to swap the one-time `code` for an access token.
        The code expires in 10 minutes and can only be used once.
        """
        logger.info(
            "GitHub OAuth token exchange | redirect_uri=%s",
            self.redirect_uri,
        )
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            response.raise_for_status()
            data = response.json()
 
        if "error" in data:
            logger.error(f"GitHub token exchange error: {data}")
            raise ValueError(f"GitHub OAuth error: {data.get('error_description', data['error'])}")
 
        token = data.get("access_token")
        if not token:
            raise ValueError("No access token in GitHub response")
 
        return token
 
    async def get_user_profile(self, access_token: str) -> GithubProfile:
        """
        Fetch the authenticated user's full profile from GitHub API.
        Makes 2 requests: /user (profile) + /user/emails (verified email).
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            user_resp = await client.get(f"{GITHUB_API_URL}/user", headers=headers)
            user_resp.raise_for_status()
            user_data = user_resp.json()
            email = user_data.get("email")

            if not email:
                try:
                    emails_resp = await client.get(
                        f"{GITHUB_API_URL}/user/emails", headers=headers
                    )
                    if emails_resp.status_code == 200:
                        emails = emails_resp.json()
                        primary = next(
                            (e for e in emails if e.get("primary") and e.get("verified")),
                            None,
                        )
                        if primary:
                            email = primary["email"]
                except Exception:
                    logger.warning("Could not fetch user emails from GitHub")

        return GithubProfile(
            github_id=user_data["id"],
            login=user_data["login"],
            email=email,
            name=user_data.get("name"),
            public_repos=user_data.get("public_repos", 0),
        )
 