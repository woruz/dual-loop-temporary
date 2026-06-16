from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class JournalAnalysis:
    id: int
    journal_id: int
    productivity_score: float
    sentiment_score: float
    goal_alignment_score: float
    risk_level: str
    feedback: str
    created_at: datetime = field(default_factory=datetime.utcnow)
