"""Unit tests for WhatsApp Webhook verification, security, and WhatsApp client."""

import hashlib
import hmac
import json
from unittest.mock import patch

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from coach_flow.config import settings
from coach_flow.main import app
from coach_flow.whatsapp.client import WhatsAppClient
from coach_flow.whatsapp.security import verify_webhook_signature


def test_signature_verification_helpers():
    secret = "secret_key_123"
    body = b'{"hello": "world"}'
    valid_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, valid_sig, secret) is True
    assert verify_webhook_signature(body, "sha256=invalid", secret) is False
    assert verify_webhook_signature(body, "", secret) is False
    assert verify_webhook_signature(body, "badprefix", secret) is False


@pytest.mark.asyncio
async def test_webhook_challenge_success():
    transport = ASGITransport(app=app)
    settings.META_WA_VERIFY_TOKEN = "test_token_123"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test_token_123",
                "hub.challenge": "challenge_accepted_42",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "challenge_accepted_42"


@pytest.mark.asyncio
async def test_webhook_challenge_forbidden():
    transport = ASGITransport(app=app)
    settings.META_WA_VERIFY_TOKEN = "correct_token"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_fail",
            },
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_incoming_button_reply():
    transport = ASGITransport(app=app)
    original_secret = settings.META_WA_APP_SECRET
    settings.META_WA_APP_SECRET = ""

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "999"},
                            "messages": [
                                {
                                    "id": "msg_btn_1",
                                    "from": "393331112222",
                                    "timestamp": "1710000000",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {
                                            "id": "confirm_appt_abc123",
                                            "title": "Confermo ✅",
                                        },
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/whatsapp/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    settings.META_WA_APP_SECRET = original_secret


@pytest.mark.asyncio
async def test_webhook_signature_validation_enforced():
    transport = ASGITransport(app=app)
    original_secret = settings.META_WA_APP_SECRET
    settings.META_WA_APP_SECRET = "super_webhook_secret"

    payload_data = {"object": "whatsapp_business_account", "entry": []}
    raw_bytes = json.dumps(payload_data).encode("utf-8")
    valid_sig = "sha256=" + hmac.new(b"super_webhook_secret", raw_bytes, hashlib.sha256).hexdigest()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid signature -> 401
        resp = await client.post(
            "/whatsapp/webhook",
            content=raw_bytes,
            headers={"X-Hub-Signature-256": "sha256=invalid", "Content-Type": "application/json"},
        )
        assert resp.status_code == 401

        # Valid signature -> 200
        resp = await client.post(
            "/whatsapp/webhook",
            content=raw_bytes,
            headers={"X-Hub-Signature-256": valid_sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200

    settings.META_WA_APP_SECRET = original_secret


@pytest.mark.asyncio
async def test_whatsapp_client_send_methods():
    client = WhatsAppClient(phone_number_id="12345", access_token="wa_token")

    async def mock_post(self, url, **kwargs):
        return httpx.Response(
            200,
            json={"messages": [{"id": "wa_msg_001"}]},
            request=httpx.Request("POST", url),
        )

    with patch.object(httpx.AsyncClient, "post", mock_post):
        # 1. Text message
        res1 = await client.send_text_message("+393331234567", "Ciao!")
        assert res1["messages"][0]["id"] == "wa_msg_001"

        # 2. Interactive buttons
        res2 = await client.send_interactive_buttons(
            "+393331234567",
            "Confermi l'appuntamento?",
            [("btn_yes", "Confermo ✅"), ("btn_no", "Annulla ❌")],
        )
        assert res2["messages"][0]["id"] == "wa_msg_001"

        # 3. Audio note
        res3 = await client.send_audio_message(
            "+393331234567",
            "https://cdn.example.com/audio/voice_note.ogg",
        )
        assert res3["messages"][0]["id"] == "wa_msg_001"

    # WhatsApp strictly allows max 3 buttons
    with pytest.raises(ValueError, match="maximum of 3 quick-reply buttons"):
        await client.send_interactive_buttons(
            "+393331234567",
            "Test",
            [("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")],
        )
