from typing import Protocol

class IEvaluatedDailyDivergence(Protocol):
    def execute(self, user_id: str) -> None:
        """Triggered by background worker to run drift score evaluation."""
        ...
