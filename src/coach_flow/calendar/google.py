"""Google Calendar Provider implementation for CoachFlow."""

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import httpx

from coach_flow.calendar.base import BaseCalendarProvider
from coach_flow.domain.models import Appointment, TimeSlot

logger = logging.getLogger(__name__)


class GoogleCalendarProvider(BaseCalendarProvider):
    """Integrates with Google Calendar API v3 using Service Account or OAuth2 token."""

    def __init__(
        self,
        calendar_id: str = "primary",
        access_token: Optional[str] = None,
        service_account_path: Optional[str] = None,
    ) -> None:
        self.calendar_id = calendar_id
        self.access_token = access_token
        self.service_account_path = service_account_path
        self.base_url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}"

    def _get_headers(self) -> dict[str, str]:
        if not self.access_token:
            # Check if access token can be resolved from env or credentials
            token = os.getenv("GOOGLE_ACCESS_TOKEN", "")
            if not token:
                raise ValueError("Google Calendar access token or service account required.")
            self.access_token = token

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def get_free_slots(
        self,
        start_date: date,
        end_date: date,
        duration_minutes: int = 60,
        buffer_minutes: int = 15,
    ) -> list[TimeSlot]:
        """Query Google Calendar freebusy endpoint to compute non-overlapping slots."""
        time_min = datetime.combine(
            start_date, datetime.min.time(), tzinfo=timezone.utc
        ).isoformat()
        time_max = datetime.combine(
            end_date, datetime.max.time(), tzinfo=timezone.utc
        ).isoformat()

        url = "https://www.googleapis.com/calendar/v3/freeBusy"
        payload = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": self.calendar_id}],
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=self._get_headers())
            resp.raise_for_status()
            data = resp.json()

        busy_intervals = data.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        busy_spans = [
            (
                datetime.fromisoformat(b["start"].replace("Z", "+00:00")),
                datetime.fromisoformat(b["end"].replace("Z", "+00:00")),
            )
            for b in busy_intervals
        ]

        # Calculate open slots
        slots: list[TimeSlot] = []
        curr = start_date
        total_step = timedelta(minutes=duration_minutes + buffer_minutes)
        slot_dur = timedelta(minutes=duration_minutes)

        while curr <= end_date:
            day_start = datetime.combine(
                curr, datetime.min.time(), tzinfo=timezone.utc
            ).replace(hour=9)
            day_end = datetime.combine(
                curr, datetime.min.time(), tzinfo=timezone.utc
            ).replace(hour=19)

            pointer = day_start
            while pointer + slot_dur <= day_end:
                cand_end = pointer + slot_dur
                is_overlap = any(
                    b_start < cand_end and b_end > pointer for b_start, b_end in busy_spans
                )
                if not is_overlap:
                    slots.append(
                        TimeSlot(start_time=pointer, end_time=cand_end, is_available=True)
                    )
                pointer += total_step
            curr += timedelta(days=1)

        return slots

    async def create_event(
        self,
        appointment: Appointment,
        client_name: str,
        client_phone: str,
        description: Optional[str] = None,
    ) -> str:
        url = f"{self.base_url}/events"
        payload = {
            "summary": f"Allenamento PT - {client_name}",
            "description": description or f"Sessione con {client_name} ({client_phone})",
            "start": {"dateTime": appointment.start_time.isoformat()},
            "end": {"dateTime": appointment.end_time.isoformat()},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=self._get_headers())
            resp.raise_for_status()
            return resp.json()["id"]

    async def reschedule_event(
        self,
        event_id: str,
        new_start: datetime,
        new_end: datetime,
    ) -> bool:
        url = f"{self.base_url}/events/{event_id}"
        payload = {
            "start": {"dateTime": new_start.isoformat()},
            "end": {"dateTime": new_end.isoformat()},
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(url, json=payload, headers=self._get_headers())
            return resp.status_code == 200

    async def cancel_event(self, event_id: str) -> bool:
        url = f"{self.base_url}/events/{event_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=self._get_headers())
            return resp.status_code in (200, 204)
