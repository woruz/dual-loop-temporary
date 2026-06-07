import uuid
from datetime import datetime
from app.core.entities import Score
from app.core.ports import ITelemetryRepository, INotificationDispatcher

class CalculateGapUseCase:
    def __init__(self, repo: ITelemetryRepository, notifier: INotificationDispatcher):
        self.repo = repo
        self.notifier = notifier

    def execute(self, user_id: str) -> None:
        print(f"[Core UseCase] Calculating divergence for user: {user_id}")
        # 1. Get identity and telemetry
        identity = self.repo.get_identity(user_id)
        if not identity:
            print(f"[Core UseCase] No identity found. Skipping.")
            return

        telemetries = self.repo.get_recent_telemetries(user_id, limit=5)
        if not telemetries:
            print(f"[Core UseCase] No recent telemetry logs. Skipping.")
            return

        # 2. Dummy calculation representing divergence (range 0.0 to 1.0)
        divergence = 0.45
        
        # 3. Save score in DB
        score = Score(
            id=str(uuid.uuid4()),
            user_id=user_id,
            divergence_score=divergence,
            calculated_at=datetime.utcnow()
        )
        self.repo.save_score(score)

        # 4. Trigger alert if divergence is above threshold (e.g. 0.4)
        if divergence > 0.4:
            self.notifier.send_divergence_alert(user_id, divergence)
