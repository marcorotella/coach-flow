"""Unit tests for Calendar Providers."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import httpx
import pytest

from coach_flow.calendar.google import GoogleCalendarProvider
from coach_flow.calendar.mock import MockCalendarProvider
from coach_flow.domain.models import Appointment


@pytest.mark.asyncio
async def test_mock_calendar_provider_free_slots():
    provider = MockCalendarProvider(daily_start_hour=10, daily_end_hour=13)
    target_date = date(2026, 11, 2)  # Monday

    # Initial query on empty calendar
    slots = await provider.get_free_slots(
        start_date=target_date,
        end_date=target_date,
        duration_minutes=60,
        buffer_minutes=15,
    )
    # 10:00-11:00, 11:15-12:15 (next would be 12:30-13:30 > 13:00) => 2 slots
    assert len(slots) == 2
    assert slots[0].start_time.hour == 10
    assert slots[1].start_time.hour == 11
    assert slots[1].start_time.minute == 15


@pytest.mark.asyncio
async def test_mock_calendar_booking_and_conflict_avoidance():
    provider = MockCalendarProvider(daily_start_hour=10, daily_end_hour=13)
    target_date = date(2026, 11, 2)

    start = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    app = Appointment(
        trainer_id="tr-1",
        client_id="cl-1",
        start_time=start,
        end_time=end,
    )

    event_id = await provider.create_event(
        app, client_name="Luca Neri", client_phone="+393330001111"
    )
    assert event_id.startswith("mock-cal-")
    assert len(provider.events) == 1

    # Now slots at 10:00 must be occupied
    slots = await provider.get_free_slots(
        start_date=target_date,
        end_date=target_date,
        duration_minutes=60,
        buffer_minutes=15,
    )
    assert len(slots) == 1
    assert slots[0].start_time.hour == 11

    # Reschedule event to 11:15
    new_start = datetime(2026, 11, 2, 11, 15, tzinfo=timezone.utc)
    new_end = new_start + timedelta(hours=1)
    rescheduled = await provider.reschedule_event(event_id, new_start, new_end)
    assert rescheduled is True
    assert provider.events[event_id]["start"] == new_start

    # Cancel event
    cancelled = await provider.cancel_event(event_id)
    assert cancelled is True
    assert len(provider.events) == 0

    # Cancel nonexistent
    assert await provider.cancel_event("unknown-id") is False
    assert await provider.reschedule_event("unknown-id", new_start, new_end) is False


def test_google_calendar_requires_token():
    with patch.dict("os.environ", {}, clear=True):
        provider = GoogleCalendarProvider(access_token=None)
        with pytest.raises(ValueError, match="access token or service account required"):
            provider._get_headers()


@pytest.mark.asyncio
async def test_google_calendar_free_slots():
    provider = GoogleCalendarProvider(calendar_id="primary", access_token="test-token")

    target_date = date(2026, 11, 2)
    fake_response = {
        "calendars": {
            "primary": {
                "busy": [
                    {
                        "start": "2026-11-02T10:00:00Z",
                        "end": "2026-11-02T11:00:00Z",
                    }
                ]
            }
        }
    }

    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, json=fake_response, request=httpx.Request("POST", url))

    with patch.object(httpx.AsyncClient, "post", mock_post):
        slots = await provider.get_free_slots(
            start_date=target_date,
            end_date=target_date,
            duration_minutes=60,
            buffer_minutes=15,
        )
        assert len(slots) > 0
        # No slot should overlap with 10:00 - 11:00
        busy_start = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
        busy_end = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)
        for s in slots:
            assert not (s.start_time < busy_end and s.end_time > busy_start)


@pytest.mark.asyncio
async def test_google_calendar_crud_lifecycle():
    provider = GoogleCalendarProvider(calendar_id="primary", access_token="test-token")

    start = datetime(2026, 11, 2, 14, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    app = Appointment(
        trainer_id="tr-1",
        client_id="cl-1",
        start_time=start,
        end_time=end,
    )

    # 1. Create event
    async def mock_create(self, url, **kwargs):
        return httpx.Response(200, json={"id": "gcal-12345"}, request=httpx.Request("POST", url))

    with patch.object(httpx.AsyncClient, "post", mock_create):
        event_id = await provider.create_event(app, "Marco", "+39333111222")
        assert event_id == "gcal-12345"

    # 2. Reschedule event
    async def mock_patch(self, url, **kwargs):
        return httpx.Response(200, json={}, request=httpx.Request("PATCH", url))

    with patch.object(httpx.AsyncClient, "patch", mock_patch):
        success = await provider.reschedule_event(
            "gcal-12345", start + timedelta(days=1), end + timedelta(days=1)
        )
        assert success is True

    # 3. Cancel event
    async def mock_delete(self, url, **kwargs):
        return httpx.Response(204, request=httpx.Request("DELETE", url))

    with patch.object(httpx.AsyncClient, "delete", mock_delete):
        success = await provider.cancel_event("gcal-12345")
        assert success is True
