from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Repository:
    id: int
    user_id: int
    repo_name: str
    repo_url: str
    created_at: datetime = field(default_factory=datetime.utcnow)
