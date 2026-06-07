from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Telemetry:
    id: str
    user_id: str
    source: str          # e.g., 'github', 'jira'
    content: str         # Text payload (PR titles, issue descriptions)
    embedding: List[float]
    timestamp: datetime
