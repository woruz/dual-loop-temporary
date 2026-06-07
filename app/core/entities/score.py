from dataclasses import dataclass
from datetime import datetime

@dataclass
class Score:
    id: str
    user_id: str
    divergence_score: float
    calculated_at: datetime
