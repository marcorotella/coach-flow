"""SQLAlchemy ORM entities for CoachFlow database persistence."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from coach_flow.storage.database import Base


class TrainerModel(Base):
    """Personal Trainer configuration and working hours."""

    __tablename__ = "trainers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    session_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    buffer_between_sessions_minutes: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False
    )
    working_hours_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ClientModel(Base):
    """Client or prospect profile undergoing fitness coaching."""

    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trainer_id: Mapped[str] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="lead", nullable=False)
    fitness_goals: Mapped[str] = mapped_column(Text, nullable=True)
    medical_notes: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_ai_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AppointmentModel(Base):
    """Scheduled coaching appointments with status and reminder tracking."""

    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trainer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    client_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    calendar_event_id: Mapped[str] = mapped_column(String(128), nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    reminder_24h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_2h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_by_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
