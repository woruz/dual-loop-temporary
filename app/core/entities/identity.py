from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class Identity:
    id: str
    user_id: str
    description: str
    embedding: List[float]
    created_at: datetime
    updated_at: datetime
