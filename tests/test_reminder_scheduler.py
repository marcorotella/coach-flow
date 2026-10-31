"""Unit tests for Reminder Scheduler and Anti No-Show automations."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from coach_flow.domain.enums import AppointmentStatus
from coach_flow.domain.models import Appointment
from coach_flow.scheduler.reminders import ReminderScheduler
from coach_flow.whatsapp.client import WhatsAppClient


@pytest.fixture
def mock_wa_client():
    client = WhatsAppClient(phone_number_id="123", access_token="token_123")
    client.send_interactive_buttons = AsyncMock(return_value={"status": "sent"})
    client.send_text_message = AsyncMock(return_value={"status": "sent"})
    return client


@pytest.mark.asyncio
async def test_scheduler_t24_and_t2_dispatch(mock_wa_client):
    now = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)

    # 1. Appointment at T+20h (due for 24h reminder)
    appt_24h = Appointment(
        id="appt_24h",
        trainer_id="tr-1",
        client_id="+393331112233",
        start_time=now + timedelta(hours=20),
        end_time=now + timedelta(hours=21),
    )

    # 2. Appointment at T+1.5h (due for 2h reminder)
    appt_2h = Appointment(
        id="appt_2h",
        trainer_id="tr-1",
        client_id="+393334445566",
        start_time=now + timedelta(hours=1, minutes=30),
        end_time=now + timedelta(hours=2, minutes=30),
    )

    # 3. Appointment cancelled (should be skipped)
    appt_cancelled = Appointment(
        id="appt_cancelled",
        trainer_id="tr-1",
        client_id="+393337778899",
        start_time=now + timedelta(hours=20),
        end_time=now + timedelta(hours=21),
        status=AppointmentStatus.CANCELLED,
    )

    # 4. Appointment far in the future at T+48h (not due)
    appt_future = Appointment(
        id="appt_future",
        trainer_id="tr-1",
        client_id="+393330001122",
        start_time=now + timedelta(hours=48),
        end_time=now + timedelta(hours=49),
    )

    appts = [appt_24h, appt_2h, appt_cancelled, appt_future]
    scheduler = ReminderScheduler(
        wa_client=mock_wa_client,
        get_appointments_fn=lambda: appts,
    )

    result = await scheduler.process_due_reminders(now=now)

    assert result["sent_24h"] == 1
    assert result["sent_2h"] == 1

    # Verify state updates
    assert appt_24h.reminder_24h_sent is True
    assert appt_2h.reminder_2h_sent is True
    assert appt_future.reminder_24h_sent is False
    assert appt_cancelled.reminder_24h_sent is False

    # Verify WhatsApp calls
    mock_wa_client.send_interactive_buttons.assert_awaited_once()
    mock_wa_client.send_text_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_scheduler_lifecycle(mock_wa_client):
    scheduler = ReminderScheduler(wa_client=mock_wa_client)
    scheduler.start(interval_minutes=1)
    assert scheduler._is_running is True

    scheduler.shutdown()
    assert scheduler._is_running is False
