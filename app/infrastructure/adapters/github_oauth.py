import httpx
import logging
from app.core.ports.oauth_port import OAuthPort, GitHubUserInfo

logger = logging.getLogger("app.infrastructure.adapters.github_oauth")

class GitHubOAuth(OAuthPort):
    _TOKEN_URL = "https://github.com/login/oauth/access_token"
    _USER_URL  = "https://api.github.com/user"
    _EMAIL_URL = "https://api.github.com/user/emails"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        logger.debug(f"GitHubOAuth initialized with client_id='{client_id[:4]}...'")

    def get_authorization_url(self, state: str) -> str:
        url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&scope=user:email"
            f"&state={state}"
        )
        logger.info(f"Generated GitHub authorization URL with state='{state}'")
        return url

    async def exchange_code(self, code: str) -> GitHubUserInfo:
        logger.info("Exchanging authorization code for GitHub access token...")
        async with httpx.AsyncClient() as client:
            # Step 1: exchange code → access token
            logger.debug(f"Sending POST request to {self._TOKEN_URL}")
            token_res = await client.post(
                self._TOKEN_URL,
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"},
            )
            token_res.raise_for_status()
            res_data = token_res.json()
            
            if "error" in res_data:
                logger.error(f"GitHub token exchange returned error: {res_data}")
                raise ValueError(f"GitHub OAuth error: {res_data.get('error_description', 'Unknown error')}")
                
            access_token = res_data.get("access_token")
            if not access_token:
                logger.error(f"GitHub token exchange did not return an access token: {res_data}")
                raise ValueError("No access token returned by GitHub")
                
            logger.info("GitHub access token successfully obtained.")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            }

            # Step 2: fetch profile
            logger.info(f"Fetching GitHub user profile from {self._USER_URL}...")
            user_res = await client.get(self._USER_URL, headers=headers)
            user_res.raise_for_status()
            user_data = user_res.json()
            logger.debug(f"GitHub user profile fetched: id='{user_data.get('id')}', login='{user_data.get('login')}'")

            # Step 3: fetch verified primary email
            # (profile email can be null if user hid it)
            email = user_data.get("email")
            if not email:
                logger.info("Profile email is null or private; fetching user emails list...")
                email_res = await client.get(self._EMAIL_URL, headers=headers)
                email_res.raise_for_status()
                emails_list = email_res.json()
                logger.debug(f"Retrieved {len(emails_list)} emails from GitHub account")
                
                primary = next(
                    (e for e in emails_list if e.get("primary") and e.get("verified")),
                    None,
                )
                if not primary:
                    logger.error("No verified primary email found on the GitHub account")
                    raise ValueError("No verified primary email on GitHub account")
                email = primary["email"]
                logger.debug(f"Selected primary verified email: '{email}'")

        logger.info(f"GitHub OAuth exchange complete. Email: '{email}', Username: '{user_data.get('login')}'")
        return GitHubUserInfo(
            provider_user_id=str(user_data["id"]),  # numeric, stable
            email=email,
            username=user_data["login"],
            avatar_url=user_data.get("avatar_url"),
        )