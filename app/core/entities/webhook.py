from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Repo:
    """
    Represents a GitHub repository entity in our domain.
    """
    name: str  
    owner_username: str
    user_id: UUID | None = None  # Links to the User if they exist in oauth_profiles
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Commit:
    """
    Represents a set of commits pushed to a repository branch.
    """
    repo_id: UUID
    branch: str
    message: dict
    total_commit: int
    pusher_username: str
    user_id: UUID | None = None  # Links to the User if they exist in oauth_profiles
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
