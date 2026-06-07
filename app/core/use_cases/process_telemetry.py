import uuid
from datetime import datetime
from app.core.entities import Telemetry
from app.core.ports import IIdentityEncoder, ITelemetryRepository

class ProcessTelemetryUseCase:
    def __init__(self, encoder: IIdentityEncoder, repo: ITelemetryRepository):
        self.encoder = encoder
        self.repo = repo

    def execute(self, user_id: str, source: str, content: str) -> None:
        print(f"[Core UseCase] Processing telemetry for {user_id} from {source}")
        # 1. Encode text payload
        embedding = self.encoder.encode(content)
        # 2. Create pure domain entity
        telemetry = Telemetry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source=source,
            content=content,
            embedding=embedding,
            timestamp=datetime.utcnow()
        )
        # 3. Save using repo port
        self.repo.save_telemetry(telemetry)
