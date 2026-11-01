"""Domain Data Models for CoachFlow."""

from datetime import datetime, time, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from coach_flow.domain.enums import AppointmentStatus, ClientStatus


class TimeSlot(BaseModel):
    """Represents a discrete time interval for a training session."""

    start_time: datetime
    end_time: datetime
    is_available: bool = True

    @model_validator(mode="after")
    def validate_slot_order(self) -> "TimeSlot":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self

    @property
    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)


class WorkingHours(BaseModel):
    """Working hours on a specific day of the week (0=Monday, 6=Sunday)."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_times(self) -> "WorkingHours":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be strictly after start_time")
        return self


class Trainer(BaseModel):
    """Personal Trainer entity profile and default scheduling rules."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., description="E.164 phone number, e.g. +393331234567")
    session_duration_minutes: int = Field(default=60, ge=15, le=240)
    buffer_between_sessions_minutes: int = Field(default=15, ge=0, le=60)
    working_hours: list[WorkingHours] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Allow 'phone' alias for phone_number
            if "phone" in data and "phone_number" not in data:
                data["phone_number"] = data["phone"]
            # Allow 'default_session_duration_minutes' alias
            if (
                "default_session_duration_minutes" in data
                and "session_duration_minutes" not in data
            ):
                data["session_duration_minutes"] = data["default_session_duration_minutes"]
            # Allow 'availability_window' alias for working_hours
            if "availability_window" in data and "working_hours" not in data:
                data["working_hours"] = data["availability_window"]
        return data

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.startswith("+") or not cleaned[1:].isdigit():
            raise ValueError("Phone number must be in E.164 format (e.g. +393331234567)")
        return cleaned

    @property
    def phone(self) -> str:
        return self.phone_number

    @property
    def default_session_duration_minutes(self) -> int:
        return self.session_duration_minutes

    @property
    def availability_window(self) -> list[WorkingHours]:
        return self.working_hours


class Client(BaseModel):
    """Lead or active client undergoing coaching."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    trainer_id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., description="E.164 phone number, e.g. +393331234567")
    status: ClientStatus = ClientStatus.LEAD
    fitness_goals: Optional[str] = None
    medical_notes: Optional[str] = None
    notes: Optional[str] = None
    is_ai_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Allow 'phone' alias for phone_number
            if "phone" in data and "phone_number" not in data:
                data["phone_number"] = data["phone"]
        return data

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        cleaned = v.replace(" ", "").replace("-", "")
        if not cleaned.startswith("+") or not cleaned[1:].isdigit():
            raise ValueError("Phone number must be in E.164 format (e.g. +393331234567)")
        return cleaned

    @property
    def phone(self) -> str:
        return self.phone_number


# Alias for conversational discovery and marketing flows
Lead = Client


class Appointment(BaseModel):
    """Represents a scheduled training session between Trainer and Client."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    trainer_id: str
    client_id: str
    calendar_event_id: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    location: Optional[str] = None
    notes: Optional[str] = None
    reminder_24h_sent: bool = False
    reminder_2h_sent: bool = False
    confirmed_by_client: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_appointment_interval(self) -> "Appointment":
        if self.end_time <= self.start_time:
            raise ValueError("Appointment end_time must be after start_time")
        return self

    @property
    def duration_minutes(self) -> int:
        return int((self.end_time - self.start_time).total_seconds() / 60)

    def confirm(self) -> None:
        """Mark appointment as confirmed by the client."""
        self.status = AppointmentStatus.CONFIRMED
        self.confirmed_by_client = True
        self.updated_at = datetime.now(timezone.utc)

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the appointment."""
        self.status = AppointmentStatus.CANCELLED
        if reason:
            self.notes = f"{self.notes or ''} [Cancelled reason: {reason}]".strip()
        self.updated_at = datetime.now(timezone.utc)

    def reschedule(self, new_start: datetime, new_end: datetime) -> None:
        """Reschedule to a new time interval."""
        if new_end <= new_start:
            raise ValueError("new_end must be strictly after new_start")
        self.start_time = new_start
        self.end_time = new_end
        self.status = AppointmentStatus.RESCHEDULED
        self.confirmed_by_client = False
        self.reminder_24h_sent = False
        self.reminder_2h_sent = False
        self.updated_at = datetime.now(timezone.utc)
