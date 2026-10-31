"""Background Reminder Scheduler for T-24h and T-2h Anti No-Show automations."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from coach_flow.config import settings
from coach_flow.domain.enums import AppointmentStatus
from coach_flow.domain.models import Appointment
from coach_flow.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Schedules and dispatches interactive T-24h and final T-2h reminders."""

    def __init__(
        self,
        wa_client: Optional[WhatsAppClient] = None,
        get_appointments_fn: Optional[Callable[[], list[Appointment]]] = None,
    ) -> None:
        self.wa_client = wa_client or WhatsAppClient()
        self.get_appointments_fn = get_appointments_fn
        self._scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self, interval_minutes: int = 5) -> None:
        """Start recurring reminder check job."""
        if not self._is_running:
            self._scheduler.add_job(
                self.process_due_reminders,
                "interval",
                minutes=interval_minutes,
                id="anti_noshow_reminders",
                replace_existing=True,
            )
            self._scheduler.start()
            self._is_running = True
            logger.info("ReminderScheduler started successfully.")

    def shutdown(self) -> None:
        """Shutdown background scheduler cleanly."""
        if self._is_running:
            self._scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("ReminderScheduler stopped.")

    async def process_due_reminders(
        self,
        now: Optional[datetime] = None,
    ) -> dict[str, int]:
        """
        Scan all active appointments and dispatch due 24h and 2h reminders.
        Returns a dict with counts of sent reminders.
        """
        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)

        appointments = self.get_appointments_fn() if self.get_appointments_fn else []

        sent_24h = 0
        sent_2h = 0

        for appt in appointments:
            if appt.status in (AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED):
                continue

            time_until_session = appt.start_time - current_time

            # Case A: T-24h window (between 23h and 25h, or <= 24h and > 2h)
            if (
                not appt.reminder_24h_sent
                and timedelta(hours=2) < time_until_session <= timedelta(hours=24)
            ):
                await self._send_24h_interactive_reminder(appt)
                appt.reminder_24h_sent = True
                sent_24h += 1

            # Case B: T-2h window (between 30min and 2h)
            elif (
                not appt.reminder_2h_sent
                and timedelta(minutes=0) < time_until_session <= timedelta(hours=2)
            ):
                await self._send_2h_final_reminder(appt)
                appt.reminder_2h_sent = True
                sent_2h += 1

        return {"sent_24h": sent_24h, "sent_2h": sent_2h}

    async def _send_24h_interactive_reminder(self, appt: Appointment) -> None:
        """Send interactive WhatsApp buttons for T-24h confirmation."""
        formatted_time = appt.start_time.strftime("%d/%m ore %H:%M")
        body_text = (
            f"Ciao! Ti ricordiamo il tuo allenamento con {settings.PT_NAME} "
            f"previsto per {formatted_time}. Ci sarai?"
        )
        buttons = [
            (f"confirm_{appt.id}", "Confermo ✅"),
            (f"reschedule_{appt.id}", "Sposta 🔄"),
            (f"cancel_{appt.id}", "Annulla ❌"),
        ]

        logger.info(f"Sending T-24h reminder to {appt.client_id} for appt {appt.id}")
        if self.wa_client.access_token:
            try:
                await self.wa_client.send_interactive_buttons(
                    to_phone=appt.client_id,
                    body_text=body_text,
                    buttons=buttons,
                )
            except Exception as exc:
                logger.error(f"Failed to send T-24h reminder to {appt.client_id}: {exc}")

    async def _send_2h_final_reminder(self, appt: Appointment) -> None:
        """Send final T-2h reminder before session."""
        body_text = (
            f"Ci vediamo tra due ore in studio per il tuo allenamento con {settings.PT_NAME}! "
            "Ricordati abbigliamento comodo e borraccia 💪"
        )

        logger.info(f"Sending T-2h reminder to {appt.client_id} for appt {appt.id}")
        if self.wa_client.access_token:
            try:
                await self.wa_client.send_text_message(
                    to_phone=appt.client_id,
                    text=body_text,
                )
            except Exception as exc:
                logger.error(f"Failed to send T-2h reminder to {appt.client_id}: {exc}")
