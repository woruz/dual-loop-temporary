"""
LOCATION: app/core/ports/auth_ports.py
 
WHY HERE: Ports are INTERFACES (contracts) that define what capabilities
the use-cases NEED, without caring HOW they're implemented.
This is the "Dependency Inversion" in SOLID — high-level code depends on
abstractions, not concrete implementations.
 
The use_case says "I need a UserRepository" — it doesn't care if it's
Postgres, MongoDB, or a dict in memory (great for testing!).
"""
 
from abc import ABC, abstractmethod
from typing import Optional
from app.core.entities import User, GithubProfile, OAuthToken 

class UserRepositoryPort(ABC):
    """
    Contract for all User persistence operations.
    Infrastructure layer MUST implement this to work with use-cases.
    """
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by our internal ID."""
        ...

    @abstractmethod
    async def get_by_github_id(self, github_id: int) -> Optional[User]: 
                """Fetch user by their GitHub ID — used during OAuth login."""

    @abstractmethod
    async def get_by_github_username(self, github_username: str) -> Optional[User]:
        """Fetch user by their GitHub username."""
        ...

    @abstractmethod
    async def create_from_github_profile(self, profile: GithubProfile, token: OAuthToken) -> User:
     """
        Create a new user from GitHub profile data.
        Called on FIRST login.
        """
    @abstractmethod
    async def update(self, user: User) -> User:
           """
        Update existing user — called on EVERY login to keep
        GitHub profile data in sync (avatar, bio, etc.)
        """
    @abstractmethod
    async def update_access_token(self, user_id: int, token:OAuthToken) -> None:
         """Update just the GitHub access token (e.g. after token refresh)."""
    
class GithubOAuthPort(ABC):
     """
    Contract for communicating with GitHub's OAuth API.
    Lets us swap GitHub for GitLab/Bitbucket without touching use-cases.
    """
     @abstractmethod
     async def exchange_code_for_token(self, code:str)-> OAuthToken:
           """
        Exchange the one-time OAuth `code` (from callback URL)
        for a GitHub access token.
        """
     @abstractmethod
     async def get_user_profile(self, access_token: OAuthToken) -> GithubProfile:
           """
        Fetch the user's GitHub profile using the access token.
        """
     @abstractmethod
     async def get_authorization_url(self,state:str)-> str:
          """Generate the Github OAuth authorization URL to redirect users to start the login flow"""""
     
class TokenServicePort(ABC):
    """
    Contract for JWT operations.
    Clean separation — use-cases don't know about JWT implementation.
    """
 
    @abstractmethod
    def create_access_token(self, user_id: int, username: str) -> str:
        ...
 
    @abstractmethod
    def create_refresh_token(self, user_id: int) -> str:
        ...
 
    @abstractmethod
    def verify_access_token(self, token: str) -> dict:
        """Returns payload dict or raises exception."""
        ...
 
    @abstractmethod
    def verify_refresh_token(self, token: str) -> dict:
        ...
    