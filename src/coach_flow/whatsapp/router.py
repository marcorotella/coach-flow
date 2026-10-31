"""Meta WhatsApp Cloud API Webhook Endpoints and Message Dispatcher."""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status

from coach_flow.config import settings
from coach_flow.whatsapp.deterministic import deterministic_handler
from coach_flow.whatsapp.models import WhatsAppWebhookPayload
from coach_flow.whatsapp.security import verify_webhook_signature

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


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
                    # AI Conversational handler will be plugged here
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


async def handle_text_message(sender_phone: str, text: str) -> None:
    """Conversational text handler (AI Agent integration)."""
    pass
