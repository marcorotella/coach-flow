"""In-memory Mock Calendar Provider for testing and local simulation."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from uuid import uuid4

from coach_flow.calendar.base import BaseCalendarProvider
from coach_flow.domain.models import Appointment, TimeSlot, WorkingHours


class MockCalendarProvider(BaseCalendarProvider):
    """In-memory calendar provider simulating Google Calendar API behavior."""

    def __init__(
        self,
        daily_start_hour: int = 9,
        daily_end_hour: int = 19,
    ) -> None:
        self.daily_start_hour = daily_start_hour
        self.daily_end_hour = daily_end_hour
        self.events: dict[str, dict] = {}

    async def get_free_slots(
        self,
        start_date: date,
        end_date: date,
        duration_minutes: int = 60,
        buffer_minutes: int = 15,
        working_hours: Optional[list[WorkingHours]] = None,
    ) -> list[TimeSlot]:
        slots: list[TimeSlot] = []
        curr_date = start_date

        total_step = timedelta(minutes=duration_minutes + buffer_minutes)
        slot_duration = timedelta(minutes=duration_minutes)

        while curr_date <= end_date:
            weekday = curr_date.weekday()

            # Determine working intervals for current day
            windows: list[tuple[datetime, datetime]] = []
            if working_hours is not None:
                day_whs = [wh for wh in working_hours if wh.day_of_week == weekday]
                for wh in day_whs:
                    w_start = datetime.combine(curr_date, wh.start_time, tzinfo=timezone.utc)
                    w_end = datetime.combine(curr_date, wh.end_time, tzinfo=timezone.utc)
                    windows.append((w_start, w_end))
            else:
                day_start = datetime.combine(
                    curr_date, time(self.daily_start_hour, 0), tzinfo=timezone.utc
                )
                day_end = datetime.combine(
                    curr_date, time(self.daily_end_hour, 0), tzinfo=timezone.utc
                )
                windows.append((day_start, day_end))

            for w_start, w_end in windows:
                current_cursor = w_start
                while current_cursor + slot_duration <= w_end:
                    slot_end = current_cursor + slot_duration

                    # Check conflict against existing scheduled events
                    is_busy = any(
                        ev["start"] < slot_end and ev["end"] > current_cursor
                        for ev in self.events.values()
                    )

                    if not is_busy:
                        slots.append(
                            TimeSlot(
                                start_time=current_cursor,
                                end_time=slot_end,
                                is_available=True,
                            )
                        )

                    current_cursor += total_step

            curr_date += timedelta(days=1)

        return slots

    async def create_event(
        self,
        appointment: Appointment,
        client_name: str,
        client_phone: str,
        description: Optional[str] = None,
    ) -> str:
        event_id = f"mock-cal-{uuid4().hex[:8]}"
        self.events[event_id] = {
            "id": event_id,
            "start": appointment.start_time,
            "end": appointment.end_time,
            "summary": f"Allenamento PT - {client_name}",
            "description": description or f"Sessione con {client_name} ({client_phone})",
        }
        return event_id

    async def reschedule_event(
        self,
        event_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> bool:
        if event_id not in self.events:
            return False
        self.events[event_id]["start"] = new_start
        self.events[event_id]["end"] = new_end
        return True

    async def cancel_event(self, event_id: str) -> bool:
        if event_id in self.events:
            del self.events[event_id]
            return True
        return False
