from dataclasses import dataclass, field 
from datetime import datetime 
from typing import Optional 

@dataclass 
class GithubProfile:
    github_id: int
    login: str            # GitHub username e.g. "torvalds"
    email: Optional[str]
    name: Optional[str]
    public_repos: int = 0


@dataclass 
class User:
    id: int
    github_id: int
    github_username: str
    email: str
    github_url: str
    is_active: bool = True
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def display_name(self) -> str:
        return self.name or self.github_username
    
    @property
    def is_email_verified(self) -> bool:
        return self.email is not None 
    

@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int = 1800 


