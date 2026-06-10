from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass
class User:
    id: UUID
    email: str
    hashed_password: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class OAuthProfile:
    id: UUID
    user_id: UUID
    provider: str
    provider_user_id: str
    created_at: datetime
    updated_at: datetime

@dataclass
class AuthToken:
    access_token: str
    token_type: str = "bearer"