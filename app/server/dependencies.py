from fastapi import Depends
from app.infrastructure.adapters import ONNXEncoder, PostgresRepository, FCMNotifier
from app.core.use_cases import OnboardUserUseCase, ProcessTelemetryUseCase, CalculateGapUseCase

# Singletons representing our concrete infrastructure adapters
_repo = PostgresRepository()
_encoder = ONNXEncoder()
_notifier = FCMNotifier()

def get_repo() -> PostgresRepository:
    return _repo

def get_encoder() -> ONNXEncoder:
    return _encoder

def get_notifier() -> FCMNotifier:
    return _notifier

# Dependency injectors for Use Cases
def get_onboard_user_use_case(
    encoder: ONNXEncoder = Depends(get_encoder),
    repo: PostgresRepository = Depends(get_repo)
) -> OnboardUserUseCase:
    return OnboardUserUseCase(encoder=encoder, repo=repo)

def get_process_telemetry_use_case(
    encoder: ONNXEncoder = Depends(get_encoder),
    repo: PostgresRepository = Depends(get_repo)
) -> ProcessTelemetryUseCase:
    return ProcessTelemetryUseCase(encoder=encoder, repo=repo)

def get_calculate_gap_use_case(
    repo: PostgresRepository = Depends(get_repo),
    notifier: FCMNotifier = Depends(get_notifier)
) -> CalculateGapUseCase:
    return CalculateGapUseCase(repo=repo, notifier=notifier)
