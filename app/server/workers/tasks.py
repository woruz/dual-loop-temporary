from app.server.workers.celery_app import celery_app
from app.server.dependencies import get_repo, get_notifier
from app.core.use_cases import CalculateGapUseCase
from app.core.entities import Identity, Telemetry
from datetime import datetime
import uuid

@celery_app.task(name="tasks.evaluate_daily_divergence")
def evaluate_daily_divergence(user_id: str) -> str:
    print(f"[Worker Task] Running celery background task: evaluate_daily_divergence for user: {user_id}")
    
    # 1. Resolve dependencies (manually, as Celery runs outside the FastAPI request context)
    repo = get_repo()
    notifier = get_notifier()
    
    # Seed mock repository if the user doesn't exist (since this is an in-memory db adapter for now)
    if not repo.get_identity(user_id):
        print(f"[Worker Task] Seeding mock database with user: {user_id}")
        repo.save_identity(Identity(
            id=str(uuid.uuid4()),
            user_id=user_id,
            description="Software Engineer",
            embedding=[0.1] * 384,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
        # Add a couple of telemetry logs
        repo.save_telemetry(Telemetry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source="github",
            content="Fixed a race condition in the message loop",
            embedding=[0.1] * 384,
            timestamp=datetime.utcnow()
        ))
        repo.save_telemetry(Telemetry(
            id=str(uuid.uuid4()),
            user_id=user_id,
            source="jira",
            content="Refactored the authentication service interface",
            embedding=[0.1] * 384,
            timestamp=datetime.utcnow()
        ))
    
    # 2. Instantiate and execute the core Use Case
    use_case = CalculateGapUseCase(repo=repo, notifier=notifier)
    use_case.execute(user_id=user_id)
    
    # Check if score was saved
    latest_score = repo.get_latest_score(user_id)
    score_val = latest_score.divergence_score if latest_score else "None"
    
    return f"Completed evaluation for {user_id}. Score saved: {score_val}"

