import logging
from fastapi import APIRouter, status, Depends, HTTPException 
from pydantic import BaseModel, EmailStr, Field

from app.server.schemas.auth import RegisterRequest, UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    use_case = Depends(lambda: None)
):
    logger.info(f"Register request received for email: {payload.email}")
    try:
        pass
    except ValueError as e:
        logger.warning(f"Registration failed for email {payload.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
