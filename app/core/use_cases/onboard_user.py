import uuid
from datetime import datetime
from app.core.entities import Identity
from app.core.ports import IIdentityEncoder, ITelemetryRepository

class OnboardUserUseCase:
    def __init__(self, encoder: IIdentityEncoder, repo: ITelemetryRepository):
        self.encoder = encoder
        self.repo = repo

    def execute(self, username: str, onboarding_description: str) -> None:
        print(f"[Core UseCase] Onboarding user: {username}")
        # 1. Encode profile description using port
        embedding = self.encoder.encode(onboarding_description)
        # 2. Create pure domain entity
        identity = Identity(
            id=str(uuid.uuid4()),
            user_id=username,
            description=onboarding_description,
            embedding=embedding,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        # 3. Save using repo port
        self.repo.save_identity(identity)
