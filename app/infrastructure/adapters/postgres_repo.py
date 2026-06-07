from typing import List, Optional, Dict
from app.core.entities import Identity, Telemetry, Score
from app.core.ports import ITelemetryRepository

class PostgresRepository:  # Note: implements ITelemetryRepository structurally
    def __init__(self):
        # Simple in-memory storage simulating a database
        self._identities: Dict[str, Identity] = {}
        self._telemetries: Dict[str, List[Telemetry]] = {}
        self._scores: Dict[str, List[Score]] = {}

    def save_identity(self, identity: Identity) -> None:
        print(f"[Adapter] PostgresRepository saving identity for: {identity.user_id}")
        self._identities[identity.user_id] = identity

    def get_identity(self, user_id: str) -> Optional[Identity]:
        print(f"[Adapter] PostgresRepository retrieving identity for: {user_id}")
        return self._identities.get(user_id)

    def save_telemetry(self, telemetry: Telemetry) -> None:
        print(f"[Adapter] PostgresRepository saving telemetry for: {telemetry.user_id}")
        if telemetry.user_id not in self._telemetries:
            self._telemetries[telemetry.user_id] = []
        self._telemetries[telemetry.user_id].append(telemetry)

    def get_recent_telemetries(self, user_id: str, limit: int = 10) -> List[Telemetry]:
        print(f"[Adapter] PostgresRepository retrieving last {limit} telemetries for: {user_id}")
        user_logs = self._telemetries.get(user_id, [])
        # Sort by timestamp descending and slice
        sorted_logs = sorted(user_logs, key=lambda x: x.timestamp, reverse=True)
        return sorted_logs[:limit]

    def save_score(self, score: Score) -> None:
        print(f"[Adapter] PostgresRepository saving divergence score: {score.divergence_score} for {score.user_id}")
        if score.user_id not in self._scores:
            self._scores[score.user_id] = []
        self._scores[score.user_id].append(score)

    def get_latest_score(self, user_id: str) -> Optional[Score]:
        print(f"[Adapter] PostgresRepository retrieving latest score for: {user_id}")
        user_scores = self._scores.get(user_id, [])
        if not user_scores:
            return None
        # Sort by calculation timestamp descending
        sorted_scores = sorted(user_scores, key=lambda x: x.calculated_at, reverse=True)
        return sorted_scores[0]
