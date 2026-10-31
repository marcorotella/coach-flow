"""Outreach service for sending authentic voice notes and discovery messages to leads."""

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from coach_flow.config import settings
from coach_flow.domain.models import Lead
from coach_flow.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)


class LeadOutreachRequest(BaseModel):
    """Payload to trigger discovery outreach for a new prospect."""

    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., description="E.164 phone number, e.g. +393331234567")
    fitness_goals: Optional[str] = None
    audio_url: Optional[str] = None
    custom_message: Optional[str] = None


class LeadOutreachService:
    """Dispatches initial greeting and authentic audio note to new leads."""

    def __init__(
        self,
        wa_client: Optional[WhatsAppClient] = None,
        default_audio_url: Optional[str] = None,
    ) -> None:
        self.wa_client = wa_client or WhatsAppClient()
        self.default_audio_url = default_audio_url or settings.DEFAULT_VOICE_MEMO_URL

    def build_intro_message(self, lead: Lead, custom_message: Optional[str] = None) -> str:
        """Constructs warm, personalized greeting text."""
        if custom_message:
            return custom_message.format(name=lead.name, pt_name=settings.PT_NAME)

        base_msg = (
            f"Ciao {lead.name}! Sono {settings.PT_NAME}, ho visto la tua richiesta "
            "per iniziare un percorso di allenamento."
        )
        if lead.fitness_goals:
            base_msg += f" Focus: {lead.fitness_goals}."

        base_msg += (
            " Ti andrebbe di fare una consulenza conoscitiva e prima valutazione "
            "in studio o online?"
        )
        return base_msg

    async def send_outreach(
        self,
        lead: Lead,
        audio_url: Optional[str] = None,
        custom_message: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Sends initial text message followed by native voice memo (OGG/Opus).
        Returns a dict summarizing dispatched messages.
        """
        intro_text = self.build_intro_message(lead, custom_message=custom_message)
        memo_url = audio_url or self.default_audio_url

        text_result = None
        audio_result = None

        logger.info(f"Dispatching discovery outreach to {lead.phone} ({lead.name})")

        # 1. Send personalized text
        if self.wa_client.access_token:
            try:
                text_result = await self.wa_client.send_text_message(
                    to_phone=lead.phone,
                    text=intro_text,
                )
            except Exception as exc:
                logger.error(f"Failed to send outreach text to {lead.phone}: {exc}")
                raise

            # 2. Send authentic audio note if available
            if memo_url:
                try:
                    audio_result = await self.wa_client.send_audio_message(
                        to_phone=lead.phone,
                        audio_url=memo_url,
                    )
                except Exception as exc:
                    logger.warning(
                        f"Failed to send voice memo to {lead.phone}: {exc}. "
                        "Text was delivered successfully."
                    )

        return {
            "status": "dispatched",
            "lead_id": lead.id,
            "recipient": lead.phone,
            "text_delivered": bool(text_result or not self.wa_client.access_token),
            "audio_delivered": bool(audio_result or (memo_url and not self.wa_client.access_token)),
            "audio_url": memo_url,
            "intro_text": intro_text,
        }
