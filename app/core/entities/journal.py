from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Journal:
    """
    Represents a daily journal entry submitted by a user.
    """
    user_id: UUID
    study_hours: float
    today_work: str
    learning_notes: str
    challenges: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
