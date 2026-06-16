from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Analysis:
    """
    Represents the AI-generated productivity, sentiment, and alignment analysis
    for a user's daily journal entry.
    """
    journal_id: UUID
    productivity_score: float
    sentiment_score: float
    goal_alignment_score: float
    risk_level: str
    missing_goal: str
    match_goal: str
    recommendation: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
