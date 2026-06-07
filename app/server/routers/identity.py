from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.server.dependencies import get_onboard_user_use_case, get_repo
from app.core.use_cases import OnboardUserUseCase
from app.infrastructure.adapters import PostgresRepository

router = APIRouter(prefix="/identity", tags=["identity"])

class OnboardRequest(BaseModel):
    username: str
    description: str

@router.post("/onboard")
def onboard_user(
    req: OnboardRequest,
    use_case: OnboardUserUseCase = Depends(get_onboard_user_use_case)
):
    try:
        use_case.execute(username=req.username, onboarding_description=req.description)
        return {"status": "success", "message": f"User {req.username} onboarded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{username}")
def get_user_identity(
    username: str,
    repo: PostgresRepository = Depends(get_repo)
):
    identity = repo.get_identity(username)
    if not identity:
        raise HTTPException(status_code=404, detail="User identity not found")
    return {
        "username": identity.user_id,
        "description": identity.description,
        "embedding_preview": identity.embedding[:5] if identity.embedding else None,
        "created_at": identity.created_at
    }
