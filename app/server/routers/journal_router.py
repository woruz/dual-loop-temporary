from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.entities.user import User
from app.core.use_cases.analyze_journal import AnalyzeJournalUseCase
from app.core.use_cases.create_goal import CreateGoalUseCase
from app.core.use_cases.create_journal import CreateJournalUseCase
from app.server.dependencies import (
    get_analyze_journal_use_case,
    get_create_goal_use_case,
    get_create_journal_use_case,
    get_current_active_user,
)

router = APIRouter(prefix="/journal", tags=["Daily Journal"])


class CreateGoalRequest(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=255)
    description: str = ""


class GoalResponse(BaseModel):
    id: int
    user_id: int
    goal_name: str
    description: str


class CreateJournalRequest(BaseModel):
    goal_id: int
    study_hours: float = Field(..., ge=0)
    today_work: str
    learning_notes: str = ""
    challenges: str = ""
    tomorrow_plan: str = ""


class JournalResponse(BaseModel):
    id: int
    user_id: int
    goal_id: int
    study_hours: float
    today_work: str
    learning_notes: str
    challenges: str
    tomorrow_plan: str
    created_at: datetime


class JournalAnalysisResponse(BaseModel):
    id: int
    journal_id: int
    productivity_score: float
    sentiment_score: float
    goal_alignment_score: float
    risk_level: str
    feedback: str
    created_at: datetime


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: CreateGoalRequest,
    current_user: User = Depends(get_current_active_user),
    use_case: CreateGoalUseCase = Depends(get_create_goal_use_case),
):
    goal = await use_case.execute(
        user_id=current_user.id,
        goal_name=body.goal_name,
        description=body.description,
    )
    return GoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        goal_name=goal.goal_name,
        description=goal.description,
    )


@router.post("/journals", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
async def create_journal(
    body: CreateJournalRequest,
    current_user: User = Depends(get_current_active_user),
    use_case: CreateJournalUseCase = Depends(get_create_journal_use_case),
):
    try:
        journal = await use_case.execute(
            user_id=current_user.id,
            goal_id=body.goal_id,
            study_hours=body.study_hours,
            today_work=body.today_work,
            learning_notes=body.learning_notes,
            challenges=body.challenges,
            tomorrow_plan=body.tomorrow_plan,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return JournalResponse(
        id=journal.id,
        user_id=journal.user_id,
        goal_id=journal.goal_id,
        study_hours=journal.study_hours,
        today_work=journal.today_work,
        learning_notes=journal.learning_notes,
        challenges=journal.challenges,
        tomorrow_plan=journal.tomorrow_plan,
        created_at=journal.created_at,
    )


@router.post(
    "/journals/{journal_id}/analyze",
    response_model=JournalAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_journal(
    journal_id: int,
    current_user: User = Depends(get_current_active_user),
    use_case: AnalyzeJournalUseCase = Depends(get_analyze_journal_use_case),
):
    try:
        analysis = await use_case.execute(user_id=current_user.id, journal_id=journal_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return JournalAnalysisResponse(
        id=analysis.id,
        journal_id=analysis.journal_id,
        productivity_score=analysis.productivity_score,
        sentiment_score=analysis.sentiment_score,
        goal_alignment_score=analysis.goal_alignment_score,
        risk_level=analysis.risk_level,
        feedback=analysis.feedback,
        created_at=analysis.created_at,
    )
