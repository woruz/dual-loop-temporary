import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.server.dependencies import (
    get_current_user,
    get_journal_repo,
    get_analysis_repo,
    get_journal_llm_adapter
)
from app.core.use_cases.create_journal import CreateJournalUseCase
from app.core.use_cases.get_journal_by_date import GetJournalByDateUseCase

logger = logging.getLogger("app.server.routers.journal")

router = APIRouter(prefix="/journal", tags=["journal"])


# ── Pydantic Request & Response Models ────────────────────────────

class JournalSubmitBody(BaseModel):
    study_hours: float = Field(..., ge=0.0, description="Number of hours spent studying/working today")
    today_work: str = Field(..., min_length=1, description="Summary of today's work")
    learning_notes: str = Field(..., min_length=1, description="Key notes and takeaways")
    challenges: str = Field(..., min_length=1, description="Challenges encountered")

class JournalResponse(BaseModel):
    study_hours: float
    today_work: str
    learning_notes: str
    challenges: str
    created_at: str

class AnalysisResponse(BaseModel):
    productivity_score: float
    sentiment_score: float
    goal_alignment_score: float
    risk_level: str
    missing_goal: str
    match_goal: str
    recommendation: str
    created_at: str

class DailyReportResponse(BaseModel):
    journal: JournalResponse
    analysis: Optional[AnalysisResponse] = None


# ── Router Endpoints ──────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_journal(
    body: JournalSubmitBody,
    user=Depends(get_current_user),
    journal_repo=Depends(get_journal_repo),
    analysis_repo=Depends(get_analysis_repo),
    llm_adapter=Depends(get_journal_llm_adapter)
):
    """
    Submits a daily journal entry, triggers Groq analysis, and saves the results.
    """
    logger.info(f"API Request: POST /journal: user email='{user.email}'")

    # 1. Enforce that the user has completed journal verification (profile has goal and experience)
    if not user.is_verified_forjournal:
        logger.warning(f"Forbidden: User '{user.email}' attempted to submit journal without journal verification.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please complete journal verification before submitting entries."
        )

    # 2. Run use case to create journal and generate analysis
    try:
        use_case = CreateJournalUseCase(journal_repo, analysis_repo, llm_adapter)
        await use_case.execute(
            user_id=user.id,
            study_hours=body.study_hours,
            today_work=body.today_work,
            learning_notes=body.learning_notes,
            challenges=body.challenges,
            user_goal=user.goal or "",
            user_experience=user.experience or ""
        )
        logger.info(f"API Success: POST /journal: user email='{user.email}' submitted journal successfully.")
        return {"message": "Journal submitted successfully and analysis is ready."}
        
    except ValueError as val_err:
        logger.warning(f"API Failure: POST /journal bad request: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        logger.exception(f"API Error: POST /journal unexpected error: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during journal submission."
        )


@router.get("/date/{date}", response_model=DailyReportResponse)
async def get_daily_report(
    date: str,
    user=Depends(get_current_user),
    journal_repo=Depends(get_journal_repo),
    analysis_repo=Depends(get_analysis_repo)
):
    """
    Retrieves the journal entry and its corresponding analysis for a specific YYYY-MM-DD date.
    All database ID fields are excluded from the returned payload.
    """
    logger.info(f"API Request: GET /journal/date/{date}: user email='{user.email}'")

    # 1. Parse date string
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"API Failure: GET /journal/date/{date}: invalid date format.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD."
        )

    # 2. Fetch journal and analysis
    use_case = GetJournalByDateUseCase(journal_repo, analysis_repo)
    result = await use_case.execute(user_id=user.id, date=parsed_date)
    
    if not result:
        logger.info(f"API Failure: GET /journal/date/{date}: report not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No journal entry found for this date"
        )

    journal, analysis = result
    
    # 3. Format response models to exclude database ID columns
    journal_resp = JournalResponse(
        study_hours=journal.study_hours,
        today_work=journal.today_work,
        learning_notes=journal.learning_notes,
        challenges=journal.challenges,
        created_at=journal.created_at.isoformat()
    )
    
    analysis_resp = None
    if analysis:
        analysis_resp = AnalysisResponse(
            productivity_score=analysis.productivity_score,
            sentiment_score=analysis.sentiment_score,
            goal_alignment_score=analysis.goal_alignment_score,
            risk_level=analysis.risk_level,
            missing_goal=analysis.missing_goal,
            match_goal=analysis.match_goal,
            recommendation=analysis.recommendation,
            created_at=analysis.created_at.isoformat()
        )

    return DailyReportResponse(journal=journal_resp, analysis=analysis_resp)
