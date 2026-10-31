"""Unit tests for deterministic Zero-LLM interactive button handling."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from coach_flow.calendar.mock import MockCalendarProvider
from coach_flow.domain.enums import AppointmentStatus
from coach_flow.domain.models import Appointment
from coach_flow.whatsapp.client import WhatsAppClient
from coach_flow.whatsapp.deterministic import (
    CANCELLATION_MESSAGE,
    CONFIRMATION_MESSAGE,
    RESCHEDULE_MESSAGE,
    DeterministicButtonHandler,
)


@pytest.fixture
def mock_wa_client():
    client = WhatsAppClient(phone_number_id="123", access_token="test_token")
    client.send_text_message = AsyncMock(return_value={"messages": [{"id": "wa_msg_reply"}]})
    return client


@pytest.fixture
def mock_calendar():
    return MockCalendarProvider()


@pytest.fixture
def sample_appointment():
    now = datetime.now(timezone.utc)
    return Appointment(
        id="appt_999",
        trainer_id="tr_1",
        client_id="cl_1",
        calendar_event_id="cal_event_999",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=1),
        status=AppointmentStatus.SCHEDULED,
    )


@pytest.mark.asyncio
async def test_confirm_button_click(mock_wa_client, sample_appointment):
    handler = DeterministicButtonHandler(wa_client=mock_wa_client)
    handler.register_appointment(sample_appointment)

    result = await handler.handle_button_click(
        sender_phone="+393331112233",
        button_id="confirm_appt_999",
        button_title="Confermo ✅",
    )

    assert result["action"] == "confirm"
    assert result["status"] == "confirmed"
    assert sample_appointment.status == AppointmentStatus.CONFIRMED
    assert sample_appointment.confirmed_by_client is True

    mock_wa_client.send_text_message.assert_awaited_once_with(
        "+393331112233", CONFIRMATION_MESSAGE
    )


@pytest.mark.asyncio
async def test_reschedule_button_click(mock_wa_client, sample_appointment):
    handler = DeterministicButtonHandler(wa_client=mock_wa_client)
    handler.register_appointment(sample_appointment)

    result = await handler.handle_button_click(
        sender_phone="+393331112233",
        button_id="reschedule_appt_999",
        button_title="Sposta data 🔄",
    )

    assert result["action"] == "reschedule"
    assert result["status"] == "rescheduled_requested"
    assert sample_appointment.confirmed_by_client is False

    mock_wa_client.send_text_message.assert_awaited_once_with(
        "+393331112233", RESCHEDULE_MESSAGE
    )


@pytest.mark.asyncio
async def test_cancel_button_click_and_calendar_removal(
    mock_wa_client, mock_calendar, sample_appointment
):
    mock_calendar.cancel_event = AsyncMock(return_value=True)

    handler = DeterministicButtonHandler(
        wa_client=mock_wa_client,
        calendar_provider=mock_calendar,
    )
    handler.register_appointment(sample_appointment)

    result = await handler.handle_button_click(
        sender_phone="+393331112233",
        button_id="cancel_appt_999",
        button_title="Annulla ❌",
    )

    assert result["action"] == "cancel"
    assert result["status"] == "cancelled"
    assert sample_appointment.status == AppointmentStatus.CANCELLED
    assert "Cancelled by client" in (sample_appointment.notes or "")

    mock_calendar.cancel_event.assert_awaited_once_with("cal_event_999")
    mock_wa_client.send_text_message.assert_awaited_once_with(
        "+393331112233", CANCELLATION_MESSAGE
    )


@pytest.mark.asyncio
async def test_unknown_button_action(mock_wa_client):
    handler = DeterministicButtonHandler(wa_client=mock_wa_client)
    result = await handler.handle_button_click(
        sender_phone="+393331112233",
        button_id="unknown_action_xyz",
    )
    assert result["action"] == "unknown"
    assert result["status"] == "unhandled"
    mock_wa_client.send_text_message.assert_not_awaited()
