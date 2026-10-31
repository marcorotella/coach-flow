"""Unit tests for domain models."""

from datetime import datetime, time, timedelta, timezone

import pytest
from pydantic import ValidationError

from coach_flow.domain.enums import AppointmentStatus, ClientStatus, InteractiveAction
from coach_flow.domain.models import Appointment, Client, Lead, TimeSlot, Trainer, WorkingHours


def test_time_slot_duration_and_validity():
    start = datetime(2026, 11, 2, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 11, 2, 11, 0, tzinfo=timezone.utc)
    slot = TimeSlot(start_time=start, end_time=end, is_available=True)

    assert slot.duration_minutes == 60
    assert slot.is_available is True

    # Invalid: end <= start
    with pytest.raises(ValidationError):
        TimeSlot(start_time=end, end_time=start)


def test_working_hours_validations():
    wh = WorkingHours(day_of_week=0, start_time=time(9, 0), end_time=time(18, 0))
    assert wh.day_of_week == 0

    # Invalid day
    with pytest.raises(ValidationError):
        WorkingHours(day_of_week=7, start_time=time(9, 0), end_time=time(18, 0))

    # Invalid hours
    with pytest.raises(ValidationError):
        WorkingHours(day_of_week=1, start_time=time(18, 0), end_time=time(9, 0))


def test_trainer_phone_validation():
    # Valid E.164
    trainer = Trainer(
        name="Alex Coach",
        phone_number="+39 333 1234567",
        default_session_duration_minutes=60,
    )
    assert trainer.phone_number == "+393331234567"
    assert trainer.phone == "+393331234567"
    assert trainer.session_duration_minutes == 60
    assert trainer.default_session_duration_minutes == 60

    # Test aliases phone and availability_window
    wh = WorkingHours(day_of_week=1, start_time=time(8, 0), end_time=time(14, 0))
    trainer_alias = Trainer(
        name="Sam Coach",
        phone="+393339876543",
        session_duration_minutes=45,
        availability_window=[wh],
    )
    assert trainer_alias.phone_number == "+393339876543"
    assert trainer_alias.session_duration_minutes == 45
    assert len(trainer_alias.availability_window) == 1

    # Invalid format without leading +
    with pytest.raises(ValidationError):
        Trainer(name="Alex Coach", phone_number="3331234567")


def test_client_defaults_and_status():
    client = Client(
        trainer_id="trainer-1",
        name="Mario Rossi",
        phone_number="+393450000000",
        fitness_goals="Perdita peso e tono muscolare",
    )
    assert client.status == ClientStatus.LEAD
    assert client.fitness_goals == "Perdita peso e tono muscolare"
    assert client.id is not None
    assert client.phone == "+393450000000"


def test_lead_alias_and_phone():
    lead = Lead(
        name="Giulia Bianchi",
        phone="+39 347 1122334",
        status=ClientStatus.PROSPECT,
        notes="Contattata via Instagram",
    )
    assert lead.name == "Giulia Bianchi"
    assert lead.phone_number == "+393471122334"
    assert lead.phone == "+393471122334"
    assert lead.status == ClientStatus.PROSPECT


def test_appointment_lifecycle():
    now = datetime.now(timezone.utc)
    start = now + timedelta(days=1)
    end = start + timedelta(hours=1)

    app = Appointment(
        trainer_id="trainer-1",
        client_id="client-1",
        start_time=start,
        end_time=end,
    )
    assert app.status == AppointmentStatus.SCHEDULED
    assert app.confirmed_by_client is False

    # Confirm action (e.g. from WhatsApp button)
    app.confirm()
    assert app.status == AppointmentStatus.CONFIRMED
    assert app.confirmed_by_client is True

    # Reschedule action
    new_start = start + timedelta(days=1)
    new_end = end + timedelta(days=1)
    app.reschedule(new_start=new_start, new_end=new_end)
    assert app.status == AppointmentStatus.RESCHEDULED
    assert app.confirmed_by_client is False
    assert app.start_time == new_start

    # Cancel action
    app.cancel(reason="Cliente impossibilitato per lavoro")
    assert app.status == AppointmentStatus.CANCELLED
    assert "Cliente impossibilitato" in (app.notes or "")


def test_appointment_invalid_interval():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        Appointment(
            trainer_id="t1",
            client_id="c1",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=1),
        )


def test_interactive_action_enum():
    assert InteractiveAction.CONFIRM.value == "confirm"
    assert InteractiveAction.RESCHEDULE.value == "reschedule"
    assert InteractiveAction.CANCEL.value == "cancel"
