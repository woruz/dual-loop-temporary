from dataclasses import dataclass


@dataclass
class Goal:
    id: int
    user_id: int
    goal_name: str
    description: str
