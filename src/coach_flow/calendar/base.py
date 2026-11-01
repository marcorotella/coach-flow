"""Abstract Base Calendar Provider interface."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Optional

from coach_flow.domain.models import Appointment, TimeSlot, WorkingHours


class BaseCalendarProvider(ABC):
    """Abstract interface defining required calendar synchronization capabilities."""

    @abstractmethod
    async def get_free_slots(
        self,
        start_date: date,
        end_date: date,
        duration_minutes: int = 60,
        buffer_minutes: int = 15,
        working_hours: Optional[list[WorkingHours]] = None,
    ) -> list[TimeSlot]:
        """Fetch available time slots between start_date and end_date."""
        pass

    @abstractmethod
    async def create_event(
        self,
        appointment: Appointment,
        client_name: str,
        client_phone: str,
        description: Optional[str] = None,
    ) -> str:
        """Create a new calendar event and return the unique external event ID."""
        pass

    @abstractmethod
    async def reschedule_event(
        self,
        event_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> bool:
        """Update event timing in the external calendar."""
        pass

    @abstractmethod
    async def cancel_event(self, event_id: str) -> bool:
        """Remove or cancel the event in the external calendar."""
        pass
