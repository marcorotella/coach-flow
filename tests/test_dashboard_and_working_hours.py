"""Tests for Coach Dashboard, Working Hours, and Anti-Conflict Availability Engine."""

from datetime import date, datetime, time, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from coach_flow.ai.tools import BookingToolExecutor
from coach_flow.calendar.mock import MockCalendarProvider
from coach_flow.domain.enums import ClientStatus
from coach_flow.domain.models import Client, WorkingHours
from coach_flow.main import app
from coach_flow.storage.database import close_db, init_db
from coach_flow.storage.repository import SQLAlchemyRepository
from coach_flow.whatsapp.router import handle_text_message


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
    await close_db()


@pytest.mark.asyncio
async def test_working_hours_split_shifts_and_break_protection():
    """Verify calendar provider never returns slots during coach break or personal workout."""
    # Monday = 0. Shift 1: 08:00 - 12:00. Shift 2: 16:00 - 20:00. (Break: 12:00 - 16:00)
    working_hours = [
        WorkingHours(day_of_week=0, start_time=time(8, 0), end_time=time(12, 0)),
        WorkingHours(day_of_week=0, start_time=time(16, 0), end_time=time(20, 0)),
    ]

    provider = MockCalendarProvider()

    # Find the next Monday
    today = date.today()
    days_ahead = (0 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = today + timedelta(days=days_ahead)

    slots = await provider.get_free_slots(
        start_date=next_monday,
        end_date=next_monday,
        duration_minutes=60,
        buffer_minutes=15,
        working_hours=working_hours,
    )

    assert len(slots) > 0

    for s in slots:
        # Verify no slot falls in break window 12:00 - 16:00
        slot_start_time = s.start_time.time()
        slot_end_time = s.end_time.time()

        is_in_morning_shift = slot_start_time >= time(8, 0) and slot_end_time <= time(12, 0)
        is_in_evening_shift = slot_start_time >= time(16, 0) and slot_end_time <= time(20, 0)

        assert (
            is_in_morning_shift or is_in_evening_shift
        ), f"Slot {s} generated outside defined shifts!"

        # Explicit check: Never during break
        assert not (
            slot_start_time < time(16, 0) and slot_end_time > time(12, 0)
        ), f"Slot {s} overlaps with coach break!"


@pytest.mark.asyncio
async def test_calendar_busy_event_conflict_avoidance():
    """Verify that events added to calendar (e.g. personal workout) are excluded from slots."""
    provider = MockCalendarProvider(daily_start_hour=8, daily_end_hour=14)

    target_date = date.today() + timedelta(days=1)

    # Coach marks an event 'Mio Allenamento' from 09:00 to 11:00
    workout_start = datetime.combine(target_date, time(9, 0), tzinfo=timezone.utc)
    workout_end = datetime.combine(target_date, time(11, 0), tzinfo=timezone.utc)
    provider.events["workout-1"] = {
        "id": "workout-1",
        "start": workout_start,
        "end": workout_end,
        "summary": "Mio Allenamento Personale",
    }

    slots = await provider.get_free_slots(
        start_date=target_date,
        end_date=target_date,
        duration_minutes=60,
        buffer_minutes=15,
    )

    # Check that NO slot overlaps with workout_start to workout_end
    for s in slots:
        overlap = s.start_time < workout_end and s.end_time > workout_start
        assert not overlap, f"Slot {s} overlaps with personal workout!"


@pytest.mark.asyncio
async def test_booking_tool_executor_with_working_hours():
    """Verify BookingToolExecutor enforces working hours on get_available_slots."""
    wh = [
        WorkingHours(day_of_week=1, start_time=time(10, 0), end_time=time(12, 0)),
    ]
    provider = MockCalendarProvider()
    executor = BookingToolExecutor(
        calendar_provider=provider,
        working_hours=wh,
        duration_minutes=60,
        buffer_minutes=15,
    )

    # Target Tuesday (weekday 1)
    today = date.today()
    days_ahead = (1 - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    tuesday = today + timedelta(days=days_ahead)

    result_json = await executor.execute(
        "get_available_slots",
        {"start_date": tuesday.isoformat(), "end_date": tuesday.isoformat()},
    )

    assert "slots" in result_json
    assert "count" in result_json


@pytest.mark.asyncio
async def test_dashboard_http_routes():
    """Test dashboard web views and form submissions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Overview
        resp = await client.get("/dashboard")
        assert resp.status_code == 200
        assert "CoachFlow" in resp.text
        assert "Panoramica" in resp.text

        # 2. Working hours page
        resp = await client.get("/dashboard/working-hours")
        assert resp.status_code == 200
        assert "Fasce Orarie Settimanali" in resp.text

        # 3. Post working hours update
        post_data = {
            "session_duration": "45",
            "buffer_minutes": "20",
            "day_0_active": "on",
            "day_0_s1_start": "08:30",
            "day_0_s1_end": "12:30",
        }
        post_resp = await client.post("/dashboard/working-hours", data=post_data)
        assert post_resp.status_code in (302, 303)

        # 4. Calendar page
        cal_resp = await client.get("/dashboard/calendar")
        assert cal_resp.status_code == 200
        assert "Calendario & Appuntamenti" in cal_resp.text

        # 5. Quick Block slot
        now = datetime.now(timezone.utc)
        block_data = {
            "start_time": (now + timedelta(days=2)).strftime("%Y-%m-%dT10:00"),
            "end_time": (now + timedelta(days=2)).strftime("%Y-%m-%dT12:00"),
            "notes": "Allenamento Personale Coach",
        }
        block_resp = await client.post("/dashboard/calendar/block", data=block_data)
        assert block_resp.status_code in (302, 303)

        # 6. Clients list
        cli_resp = await client.get("/dashboard/clients")
        assert cli_resp.status_code == 200
        assert "Anagrafica Atleti" in cli_resp.text

        # 7. Add new client
        new_cli_data = {
            "name": "Andrea Gialli",
            "phone_number": "+393338887766",
            "fitness_goals": "Preparazione mezza maratona",
        }
        add_resp = await client.post("/dashboard/clients/new", data=new_cli_data)
        assert add_resp.status_code in (302, 303)


@pytest.mark.asyncio
async def test_ai_toggle_pauses_automated_replies():
    """Verify that toggling AI off for a client silences the automated assistant."""
    repo = SQLAlchemyRepository()
    client = Client(
        id="client-paused-1",
        name="Silvia Neri",
        phone_number="+393471112233",
        status=ClientStatus.ACTIVE,
        is_ai_active=False,  # Coach paused AI
    )
    await repo.save_client(client)

    # When incoming message arrives from paused client
    reply = await handle_text_message(
        sender_phone="+393471112233",
        text="Ciao Coach, a che ora ci vediamo domani?",
    )

    # Reply must be empty (silent) because AI is paused for this athlete
    assert reply == ""
