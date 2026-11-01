"""Meta WhatsApp Cloud API Webhook Endpoints and Message Dispatcher."""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status

from coach_flow.ai import get_ai_provider
from coach_flow.ai.agent import BookingAgent
from coach_flow.ai.mock import MockAIProvider
from coach_flow.calendar.mock import MockCalendarProvider
from coach_flow.config import settings
from coach_flow.whatsapp.client import WhatsAppClient
from coach_flow.whatsapp.deterministic import deterministic_handler
from coach_flow.whatsapp.models import WhatsAppWebhookPayload
from coach_flow.whatsapp.security import verify_webhook_signature

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


def _create_default_agent() -> BookingAgent:
    try:
        ai_provider = get_ai_provider()
    except Exception:
        ai_provider = MockAIProvider()
    calendar_provider = MockCalendarProvider()
    return BookingAgent(ai_provider=ai_provider, calendar_provider=calendar_provider)


# Module-level instances for message handling
booking_agent: BookingAgent = _create_default_agent()
whatsapp_client: WhatsAppClient = WhatsAppClient()
_trainer_assistant: Any = None


def get_trainer_assistant():
    global _trainer_assistant
    if _trainer_assistant is None:
        from coach_flow.assistant.trainer import TrainerAssistantService

        _trainer_assistant = TrainerAssistantService()
    return _trainer_assistant


@router.get("/webhook")
async def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """
    Verification endpoint required by Meta WhatsApp when registering webhook.
    Returns hub.challenge if hub.verify_token matches META_WA_VERIFY_TOKEN.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.META_WA_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully.")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("WhatsApp webhook verification failed.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch",
    )


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    Receives incoming webhook events from Meta WhatsApp Cloud API.
    Validates HMAC signature and routes to deterministic button handler or AI.
    """
    raw_body = await request.body()

    # Verify signature in production or if app secret is provided
    if settings.META_WA_APP_SECRET:
        if not x_hub_signature_256 or not verify_webhook_signature(
            raw_body, x_hub_signature_256, settings.META_WA_APP_SECRET
        ):
            logger.error("Invalid HMAC signature on WhatsApp webhook")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    try:
        data = await request.json()
        payload = WhatsAppWebhookPayload.model_validate(data)
    except Exception as exc:
        logger.warning(f"Ignored non-message webhook payload: {exc}")
        return {"status": "ignored"}

    # Process messages
    for entry in payload.entry:
        for change in entry.changes:
            messages = change.value.messages or []
            for msg in messages:
                sender_phone = msg.from_

                # Case 1: Interactive quick reply button (Zero-LLM cost)
                if msg.type == "interactive" and msg.interactive and msg.interactive.button_reply:
                    btn_id = msg.interactive.button_reply.id
                    btn_title = msg.interactive.button_reply.title
                    logger.info(
                        f"Button click from {sender_phone}: ID={btn_id}, Title={btn_title}"
                    )
                    await handle_interactive_button(sender_phone, btn_id, btn_title)

                # Case 2: Free text message
                elif msg.type == "text" and msg.text:
                    user_text = msg.text.body
                    logger.info(f"Incoming text from {sender_phone}: {user_text}")
                    await handle_text_message(sender_phone, user_text)

    return {"status": "ok"}


async def handle_interactive_button(
    sender_phone: str,
    button_id: str,
    button_title: Optional[str] = None,
) -> dict[str, Any]:
    """Zero-LLM deterministic action dispatcher for button replies."""
    return await deterministic_handler.handle_button_click(
        sender_phone=sender_phone,
        button_id=button_id,
        button_title=button_title,
    )


async def handle_text_message(sender_phone: str, text: str) -> str:
    """Conversational text handler (AI Agent integration)."""
    from coach_flow.assistant.trainer import HANDOVER_ACK_MESSAGE, TrainerAssistantService
    from coach_flow.storage.repository import repository

    # Check if AI is explicitly paused for this client from Dashboard
    client = await repository.get_client_by_phone(sender_phone)
    if client and not client.is_ai_active:
        logger.info(f"AI is paused for client {sender_phone}. Skipping automated reply.")
        return ""

    if TrainerAssistantService.check_handover_intent(text):
        assistant = get_trainer_assistant()
        await assistant.trigger_human_handover(
            sender_phone=sender_phone,
            reason=f"Richiesta esplicita cliente: '{text}'",
        )
        reply = HANDOVER_ACK_MESSAGE
    else:
        reply = await booking_agent.handle_incoming_message(sender_phone, text)

    if whatsapp_client.access_token:
        try:
            await whatsapp_client.send_text_message(sender_phone, reply)
        except Exception as exc:
            logger.warning(f"Could not send WhatsApp text reply to {sender_phone}: {exc}")
    return reply
