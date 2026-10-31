"""Unit tests for SQLAlchemy async database storage and repository."""

from datetime import date, datetime, time, timedelta, timezone

import pytest

from coach_flow.domain.enums import AppointmentStatus, ClientStatus
from coach_flow.domain.models import Appointment, Client, Trainer, WorkingHours
from coach_flow.storage.database import close_db, init_db
from coach_flow.storage.repository import SQLAlchemyRepository


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
    await close_db()


@pytest.mark.asyncio
async def test_client_crud_lifecycle():
    repo = SQLAlchemyRepository()

    client = Client(
        id="client-test-1",
        trainer_id="tr-1",
        name="Giovanni Rossi",
        phone_number="+393339991122",
        status=ClientStatus.ACTIVE,
        fitness_goals="Ricostruzione post-infortunio",
    )

    # 1. Save
    saved = await repo.save_client(client)
    assert saved.id == "client-test-1"

    # 2. Get by phone
    fetched = await repo.get_client_by_phone("+39 333 999 1122")
    assert fetched is not None
    assert fetched.name == "Giovanni Rossi"
    assert fetched.status == ClientStatus.ACTIVE

    # 3. Update
    client.notes = "Seduta settimanale mercoledì"
    client.status = ClientStatus.PAUSED
    await repo.save_client(client)

    updated = await repo.get_client_by_id("client-test-1")
    assert updated is not None
    assert updated.status == ClientStatus.PAUSED
    assert updated.notes == "Seduta settimanale mercoledì"


@pytest.mark.asyncio
async def test_appointment_crud_and_queries():
    repo = SQLAlchemyRepository()
    now = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)

    appt1 = Appointment(
        id="appt-test-1",
        trainer_id="tr-1",
        client_id="cl-1",
        calendar_event_id="cal-123",
        start_time=now,
        end_time=now + timedelta(hours=1),
        status=AppointmentStatus.SCHEDULED,
        notes="Valutazione iniziale",
    )

    appt2 = Appointment(
        id="appt-test-2",
        trainer_id="tr-1",
        client_id="cl-2",
        calendar_event_id="cal-456",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        status=AppointmentStatus.CONFIRMED,
    )

    # 1. Save both
    await repo.save_appointment(appt1)
    await repo.save_appointment(appt2)

    # 2. Get by ID
    res1 = await repo.get_appointment("appt-test-1")
    assert res1 is not None
    assert res1.notes == "Valutazione iniziale"
    assert res1.calendar_event_id == "cal-123"

    # 3. Query by date
    day1_appts = await repo.get_appointments_by_date(date(2026, 11, 2))
    assert len(day1_appts) >= 1
    assert any(a.id == "appt-test-1" for a in day1_appts)

    # 4. Get all appointments
    all_appts = await repo.get_all_appointments()
    assert len(all_appts) >= 2

    # 5. Delete appointment
    deleted = await repo.delete_appointment("appt-test-1")
    assert deleted is True
    assert await repo.get_appointment("appt-test-1") is None


@pytest.mark.asyncio
async def test_trainer_crud_with_working_hours():
    repo = SQLAlchemyRepository()

    wh1 = WorkingHours(day_of_week=0, start_time=time(8, 0), end_time=time(14, 0))
    wh2 = WorkingHours(day_of_week=2, start_time=time(14, 0), end_time=time(20, 0))

    trainer = Trainer(
        id="trainer-test-1",
        name="Coach Andrea",
        phone_number="+393478889900",
        session_duration_minutes=50,
        buffer_between_sessions_minutes=10,
        working_hours=[wh1, wh2],
    )

    await repo.save_trainer(trainer)

    fetched = await repo.get_trainer("trainer-test-1")
    assert fetched is not None
    assert fetched.name == "Coach Andrea"
    assert fetched.session_duration_minutes == 50
    assert len(fetched.working_hours) == 2
    assert fetched.working_hours[0].day_of_week == 0
    assert fetched.working_hours[1].day_of_week == 2
