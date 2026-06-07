from fastapi import APIRouter, Depends, HTTPException
from app.server.dependencies import get_repo
from app.infrastructure.adapters import PostgresRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/{user_id}")
def get_user_dashboard(
    user_id: str,
    repo: PostgresRepository = Depends(get_repo)
):
    identity = repo.get_identity(user_id)
    if not identity:
        raise HTTPException(status_code=404, detail="User not found")
        
    telemetries = repo.get_recent_telemetries(user_id, limit=5)
    latest_score = repo.get_latest_score(user_id)
    
    return {
        "user_id": user_id,
        "description": identity.description,
        "latest_score": latest_score.divergence_score if latest_score else None,
        "calculated_at": latest_score.calculated_at if latest_score else None,
        "recent_telemetries_count": len(telemetries),
        "recent_telemetries": [
            {
                "source": t.source,
                "content": t.content,
                "timestamp": t.timestamp
            } for t in telemetries
        ]
    }
