"""FastAPI router for prospect discovery and outreach triggering."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from coach_flow.discovery.outreach import LeadOutreachRequest, LeadOutreachService
from coach_flow.domain.models import Lead

router = APIRouter(prefix="/discovery", tags=["Discovery & Outreach"])
outreach_service = LeadOutreachService()


@router.post("/outreach", status_code=status.HTTP_200_OK)
async def trigger_lead_outreach(request: LeadOutreachRequest) -> dict[str, Any]:
    """
    Trigger initial outreach (text + authentic voice note) to a new prospect.
    Called when a new lead enters via CRM, webhook, landing page, or spreadsheet.
    """
    try:
        lead = Lead(
            name=request.name,
            phone=request.phone,
            fitness_goals=request.fitness_goals,
        )
        result = await outreach_service.send_outreach(
            lead=lead,
            audio_url=request.audio_url,
            custom_message=request.custom_message,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outreach failed: {exc}",
        )
