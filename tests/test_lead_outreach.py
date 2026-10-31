"""Unit tests for Lead Discovery Outreach and Voice Note dispatch."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from coach_flow.discovery.outreach import LeadOutreachService
from coach_flow.domain.models import Lead
from coach_flow.main import app
from coach_flow.whatsapp.client import WhatsAppClient


@pytest.fixture
def mock_wa_client():
    client = WhatsAppClient(phone_number_id="12345", access_token="wa_test_token")
    client.send_text_message = AsyncMock(return_value={"messages": [{"id": "txt_123"}]})
    client.send_audio_message = AsyncMock(return_value={"messages": [{"id": "aud_123"}]})
    return client


def test_build_intro_message():
    service = LeadOutreachService()
    lead = Lead(
        name="Giulia",
        phone="+393331112233",
        fitness_goals="Tonificazione e postura",
    )
    msg = service.build_intro_message(lead)
    assert "Giulia" in msg
    assert "Tonificazione e postura" in msg

    # Custom template
    custom = service.build_intro_message(
        lead,
        custom_message="Ehi {name}, pronto ad allenarti con {pt_name}?",
    )
    assert "Ehi Giulia, pronto ad allenarti con" in custom


@pytest.mark.asyncio
async def test_send_outreach_text_and_audio(mock_wa_client):
    service = LeadOutreachService(
        wa_client=mock_wa_client,
        default_audio_url="https://cdn.example.com/audio/pt_intro.ogg",
    )
    lead = Lead(name="Lorenzo", phone="+393339990011")

    res = await service.send_outreach(lead)
    assert res["status"] == "dispatched"
    assert res["recipient"] == "+393339990011"
    assert res["text_delivered"] is True
    assert res["audio_delivered"] is True
    assert res["audio_url"] == "https://cdn.example.com/audio/pt_intro.ogg"

    mock_wa_client.send_text_message.assert_awaited_once()
    mock_wa_client.send_audio_message.assert_awaited_once_with(
        to_phone="+393339990011",
        audio_url="https://cdn.example.com/audio/pt_intro.ogg",
    )


@pytest.mark.asyncio
async def test_send_outreach_audio_failure_is_resilient(mock_wa_client):
    mock_wa_client.send_audio_message = AsyncMock(side_effect=Exception("Audio upload failed"))
    service = LeadOutreachService(
        wa_client=mock_wa_client,
        default_audio_url="https://cdn.example.com/audio/pt_intro.ogg",
    )
    lead = Lead(name="Serena", phone="+393450001122")

    # Should not crash; text is delivered and audio failure is logged
    res = await service.send_outreach(lead)
    assert res["status"] == "dispatched"
    assert res["text_delivered"] is True
    assert res["audio_delivered"] is False


@pytest.mark.asyncio
async def test_discovery_outreach_api_endpoint(mock_wa_client):
    transport = ASGITransport(app=app)
    from coach_flow.discovery.router import outreach_service

    outreach_service.wa_client = mock_wa_client

    payload = {
        "name": "Federico",
        "phone": "+393337778899",
        "fitness_goals": "Ipertrofia e forza",
        "audio_url": "https://cdn.example.com/audio/memo.ogg",
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/discovery/outreach", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "dispatched"
        assert data["recipient"] == "+393337778899"


@pytest.mark.asyncio
async def test_discovery_outreach_invalid_phone():
    transport = ASGITransport(app=app)
    payload = {
        "name": "Federico",
        "phone": "invalid-phone",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/discovery/outreach", json=payload)
        assert resp.status_code == 500
