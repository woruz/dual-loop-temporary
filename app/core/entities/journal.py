from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Journal:
    id: int
    user_id: int
    goal_id: int
    study_hours: float
    today_work: str
    learning_notes: str
    challenges: str
    tomorrow_plan: str
    created_at: datetime = field(default_factory=datetime.utcnow)
