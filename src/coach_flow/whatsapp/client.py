"""Client for Meta WhatsApp Cloud API."""

import logging
from typing import Any, Optional

import httpx

from coach_flow.config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Sends outbound messages via Meta WhatsApp Cloud API v19.0."""

    def __init__(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
    ) -> None:
        self.phone_number_id = phone_number_id or settings.META_WA_PHONE_NUMBER_ID
        self.access_token = access_token or settings.META_WA_ACCESS_TOKEN
        self.base_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(self, to_phone: str, text: str) -> dict[str, Any]:
        """Send a standard text message to a recipient."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone.replace("+", ""),
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.base_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def send_interactive_buttons(
        self,
        to_phone: str,
        body_text: str,
        buttons: list[tuple[str, str]],
    ) -> dict[str, Any]:
        """
        Send an interactive message with up to 3 quick-reply buttons.
        buttons: list of (button_id, button_title) tuples.
        """
        if len(buttons) > 3:
            raise ValueError("WhatsApp allows a maximum of 3 quick-reply buttons per message")

        button_objects = [
            {
                "type": "reply",
                "reply": {
                    "id": b_id,
                    "title": b_title[:20],  # WhatsApp max title length is 20 chars
                },
            }
            for b_id, b_title in buttons
        ]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone.replace("+", ""),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": button_objects},
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.base_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def send_audio_message(self, to_phone: str, audio_url: str) -> dict[str, Any]:
        """
        Send an authentic audio note/voice memo.
        Meta renders audio/ogg (Opus) natively as a voice note.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone.replace("+", ""),
            "type": "audio",
            "audio": {"link": audio_url},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.base_url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
