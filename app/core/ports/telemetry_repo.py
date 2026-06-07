from typing import Protocol, List, Optional
from app.core.entities import Identity, Telemetry, Score

class ITelemetryRepository(Protocol):
    def save_identity(self, identity: Identity) -> None:
        """Saves a user's semantic identity."""
        ...

    def get_identity(self, user_id: str) -> Optional[Identity]:
        """Retrieves a user's semantic identity."""
        ...

    def save_telemetry(self, telemetry: Telemetry) -> None:
        """Saves a single telemetry event (PR or commit log)."""
        ...

    def get_recent_telemetries(self, user_id: str, limit: int = 10) -> List[Telemetry]:
        """Retrieves recent telemetry logs for a user."""
        ...

    def save_score(self, score: Score) -> None:
        """Saves a calculated divergence score."""
        ...

    def get_latest_score(self, user_id: str) -> Optional[Score]:
        """Retrieves the latest calculated divergence score for a user."""
        ...
