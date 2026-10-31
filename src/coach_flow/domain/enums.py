"""Domain Enumerations for CoachFlow."""

from enum import Enum


class ClientStatus(str, Enum):
    """Lifecycle status of a fitness client or prospect."""
    LEAD = "lead"
    PROSPECT = "prospect"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class AppointmentStatus(str, Enum):
    """Status of a scheduled training session."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class InteractiveAction(str, Enum):
    """Actions received from WhatsApp interactive buttons."""
    CONFIRM = "confirm"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
