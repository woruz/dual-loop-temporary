"""
LOCATION: app/core/use_cases/auth_use_cases.py
 
WHY HERE: Use-cases contain your BUSINESS LOGIC — the "what does our app do?"
They orchestrate entities and ports but know NOTHING about HTTP, databases, or GitHub.
 
This is the most important layer. It's 100% unit-testable with mock ports.
If GitHub changes their API, only the adapter changes — use-cases stay the same.
"""
import secrets
import logging
from app.core.entities import User, OAuthToken, GithubProfile
from app.core.ports.auth_ports import UserRepositoryPort,GithubOAuthPort,TokenServicePort


logger = logging.getLogger(__name__)

class GithubAuthUseCase:
     """
    Orchestrates the full GitHub OAuth flow:
    1. Generate OAuth URL (with CSRF protection)
    2. Handle callback → exchange code → fetch profile → upsert user → issue JWTs
 
    Injected via dependency injection (see dependencies.py).
    No imports from infrastructure or server layers — pure business logic.
    """
     def __init__(self,user_repo: UserRepositoryPort, oauth_port: GithubOAuthPort, token_service: TokenServicePort):
          self.user_repo = user_repo
          self.oauth_port = oauth_port
          self.token_service = token_service
        
     def get_ouauth_url(self) -> str:
          
          """
        Returns (authorization_url, state).
        The `state` is a CSRF token — store it in the session/cookie,
        verify it matches when GitHub redirects back.
        """
    
          state = secrets.token_urlsafe(32)
          url = self.oauth_port.get_authorization_url(state)
          logger.info(f"Generated Github OAuth URL with state:")
          return url,state
     async def handle_callback(self, code: str, state: str, expected_state: str) -> tuple[OAuthToken, User]:
        """
        Full OAuth callback flow. Called when GitHub redirects to /auth/github/callback.
 
        Args:
            code: One-time code from GitHub
            state: State param from GitHub (must match expected_state)
            expected_state: What we stored in the session when we started OAuth
 
        Returns:
            (OAuthToken, User) — tokens for client, user for logging/response
 
        Raises:
            ValueError: on CSRF mismatch or GitHub API errors
        """
        # 1. CSRF check — prevent state forgery attacks
        if state != expected_state:
            logger.warning("OAuth state mismatch — possible CSRF attack")
            raise ValueError("Invalid OAuth state — please try logging in again")
 
        # 2. Exchange one-time code → GitHub access token
        logger.info("Exchanging OAuth code for GitHub access token")
        github_token = await self.github_oauth.exchange_code_for_token(code)

        #3. Fetch User's Github Profile using access token 
        logger.info("Fetching user profile from Github")
        profile = await self.github_oauth.get_user_profile(github_token)

        #4. Upsert User in our database (create if new, update if existing)
        existing_user = await self.user_repo.get_by_github_username(profile.github_id)

        if existing_user:
            ##Update exisiting user in the case they change their Github PROfile 
            existing_user.github_username = profile.login
            existing_user.email = profile.email
            user = await self.user_repo.update(existing_user)
            await self.user_repo.update_access_token(user.id,github_token)
            logger.info(f"Existing user logged in: {user.username} (id={user.id})")
        else:
            user = await self.user_repo.create(profile,github_token)
            logger.info(f"New user registered via GitHub: {user.username} (id={user.id})")

        ##5. Issues own JWTs
        access_token = self.token_service.create_access_token(self.user.id, user.username)
        refresh_token = self.token_service.create_refresh_token(user.id)
        tokens = OAuthToken(access_token=access_token,refresh_token=refresh_token)
        return tokens,user
     async def refresh_tokens(self, refresh_token: str) -> OAuthToken:
        """
        Issue new access token using a valid refresh token.
        Called when the 30-min access token expires.
        """
        payload = self.token_service.verify_refresh_token(refresh_token)
        user_id = int(payload["sub"])
 
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")
        
        new_access = self.token_service.create_access_token(user.id,user.username)
        new_refresh = self.token_service.create_refresh_token(user.id)

        
        return OAuthToken(access_token=new_access, refresh_token=new_refresh)
     
     async def get_current_user(self, access_token: str) -> User:
        """Validate JWT and return the user. Used by auth middleware."""
        payload = self.token_service.verify_access_token(access_token)
        user_id = int(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or deactivated")
        return user
     
    
     
    
         
 
   