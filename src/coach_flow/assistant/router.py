"""FastAPI router for Trainer Daily Digest and Human Handover endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from coach_flow.assistant.trainer import TrainerAssistantService

router = APIRouter(prefix="/assistant", tags=["Trainer Assistant"])
assistant_service = TrainerAssistantService()


class HandoverRequest(BaseModel):
    sender_phone: str = Field(..., description="E.164 phone number of the client")
    user_name: Optional[str] = None
    reason: Optional[str] = None


@router.post("/handover", status_code=status.HTTP_200_OK)
async def trigger_handover(req: HandoverRequest) -> dict[str, Any]:
    """Trigger human handover emergency alert to Personal Trainer."""
    try:
        return await assistant_service.trigger_human_handover(
            sender_phone=req.sender_phone,
            user_name=req.user_name,
            reason=req.reason,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Handover failed: {exc}",
        )
