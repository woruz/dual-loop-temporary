from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.server.dependencies import get_process_telemetry_use_case, get_calculate_gap_use_case
from app.core.use_cases import ProcessTelemetryUseCase, CalculateGapUseCase

router = APIRouter(prefix="/webhook", tags=["webhook"])

class WebhookPayload(BaseModel):
    user_id: str
    source: str
    content: str

@router.post("/telemetry")
def receive_telemetry(
    payload: WebhookPayload,
    process_use_case: ProcessTelemetryUseCase = Depends(get_process_telemetry_use_case),
    calculate_use_case: CalculateGapUseCase = Depends(get_calculate_gap_use_case)
):
    try:
        # 1. Process and save telemetry
        process_use_case.execute(
            user_id=payload.user_id,
            source=payload.source,
            content=payload.content
        )
        
        # 2. Trigger divergence calculations immediately for validation
        calculate_use_case.execute(user_id=payload.user_id)
        
        return {"status": "success", "message": "Telemetry processed and evaluation complete"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
