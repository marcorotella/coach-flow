"""Unit tests for Trainer Daily Digest agenda and Human Handover emergency alert."""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from coach_flow.assistant.trainer import (
    HANDOVER_ACK_MESSAGE,
    TrainerAssistantService,
)
from coach_flow.config import settings
from coach_flow.domain.models import Appointment
from coach_flow.main import app
from coach_flow.whatsapp.client import WhatsAppClient


@pytest.fixture
def mock_wa_client():
    client = WhatsAppClient(phone_number_id="123", access_token="token_pt")
    client.send_text_message = AsyncMock(return_value={"messages": [{"id": "msg_pt_1"}]})
    return client


def test_generate_daily_digest_empty():
    service = TrainerAssistantService()
    target_date = date(2026, 11, 2)
    digest = service.generate_daily_digest([], target_date=target_date)
    assert "Nessuna sessione in programma" in digest


def test_generate_daily_digest_with_appointments():
    service = TrainerAssistantService()
    target_date = date(2026, 11, 2)

    appt1 = Appointment(
        trainer_id="tr-1",
        client_id="+393331112233",
        start_time=datetime(2026, 11, 2, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc),
        confirmed_by_client=True,
        notes="Scheda Gambe / Focus Squat",
    )
    appt2 = Appointment(
        trainer_id="tr-1",
        client_id="+393334445566",
        start_time=datetime(2026, 11, 2, 11, 15, tzinfo=timezone.utc),
        end_time=datetime(2026, 11, 2, 12, 15, tzinfo=timezone.utc),
        confirmed_by_client=False,
    )

    digest = service.generate_daily_digest([appt1, appt2], target_date=target_date)
    assert "09:00 - 10:00" in digest
    assert "✅ Confermato" in digest
    assert "Focus Squat" in digest
    assert "11:15 - 12:15" in digest
    assert "⏳ In attesa di conferma" in digest
    assert "Totale sessioni oggi: *2*" in digest


@pytest.mark.asyncio
async def test_send_daily_digest_dispatches_to_pt(mock_wa_client):
    service = TrainerAssistantService(
        wa_client=mock_wa_client,
        pt_phone="+393330009988",
    )
    res = await service.send_daily_digest([], target_date=date(2026, 11, 2))
    assert res["status"] == "sent"
    assert res["recipient"] == "+393330009988"
    mock_wa_client.send_text_message.assert_awaited_once()


def test_check_handover_intent_detection():
    assert (
        TrainerAssistantService.check_handover_intent("Vorrei parlare con il coach di persona")
        is True
    )
    assert TrainerAssistantService.check_handover_intent("Passami un umano per favore") is True
    assert TrainerAssistantService.check_handover_intent("Ho un forte dolore al ginocchio") is True
    assert (
        TrainerAssistantService.check_handover_intent("Ciao, vorrei sapere quali orari hai liberi")
        is False
    )


@pytest.mark.asyncio
async def test_trigger_human_handover_alert(mock_wa_client):
    service = TrainerAssistantService(
        wa_client=mock_wa_client,
        pt_phone="+393330009988",
    )
    res = await service.trigger_human_handover(
        sender_phone="+393331122334",
        user_name="Marco Rossi",
        reason="Dubbi sull'infortunio alla spalla",
    )
    assert res["status"] == "handover_alerted"
    assert res["ack_message_to_client"] == HANDOVER_ACK_MESSAGE
    assert "https://wa.me/393331122334" in res["alert_text"]
    mock_wa_client.send_text_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_handover_endpoint_integration(mock_wa_client):
    transport = ASGITransport(app=app)
    from coach_flow.assistant.router import assistant_service

    assistant_service.wa_client = mock_wa_client
    assistant_service.pt_phone = "+393330009988"

    payload = {
        "sender_phone": "+393451122334",
        "user_name": "Chiara",
        "reason": "Richiesta chiarimento piano nutrizionale",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/assistant/handover", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "handover_alerted"


@pytest.mark.asyncio
async def test_webhook_handover_automatic_interception(mock_wa_client):
    transport = ASGITransport(app=app)
    from coach_flow.whatsapp.router import get_trainer_assistant

    assistant = get_trainer_assistant()
    assistant.wa_client = mock_wa_client
    assistant.pt_phone = "+393330009988"

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
                                    "id": "msg_handover_1",
                                    "from": "393331112222",
                                    "timestamp": "1710000000",
                                    "type": "text",
                                    "text": {"body": "Vorrei parlare con il coach direttamente"},
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

    settings.META_WA_APP_SECRET = original_secret
