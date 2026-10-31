"""Deterministic zero-LLM interactive button event processor."""

import logging
from typing import Any, Optional

from coach_flow.calendar.base import BaseCalendarProvider
from coach_flow.domain.models import Appointment
from coach_flow.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

CONFIRMATION_MESSAGE = (
    "Ottimo! La tua sessione di allenamento è confermata ✅ Ci vediamo in studio!"
)
RESCHEDULE_MESSAGE = (
    "Nessun problema! Scrivimi pure che giorno e orario preferiresti per recuperare "
    "la sessione 🔄"
)
CANCELLATION_MESSAGE = (
    "Ricevuto! La tua sessione è stata cancellata ❌ "
    "Se vorrai riprenotare, puoi scriverci qui in qualsiasi momento."
)


class DeterministicButtonHandler:
    """Processes quick-reply button clicks with sub-second latency and zero LLM cost."""

    def __init__(
        self,
        wa_client: Optional[WhatsAppClient] = None,
        calendar_provider: Optional[BaseCalendarProvider] = None,
        appointments_db: Optional[dict[str, Appointment]] = None,
    ) -> None:
        self.wa_client = wa_client or WhatsAppClient()
        self.calendar_provider = calendar_provider
        # In-memory dictionary acting as appointment store when no external DB is plugged
        self.appointments_db: dict[str, Appointment] = (
            appointments_db if appointments_db is not None else {}
        )

    def register_appointment(self, appointment: Appointment) -> None:
        """Register an active appointment in the local lookup table."""
        self.appointments_db[appointment.id] = appointment

    async def handle_button_click(
        self,
        sender_phone: str,
        button_id: str,
        button_title: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Parse button ID prefix, execute business logic, and dispatch immediate WhatsApp reply.
        Returns a dict describing the action performed.
        """
        logger.info(
            f"Deterministic dispatch for {sender_phone}: "
            f"button_id='{button_id}', title='{button_title}'"
        )

        action = None
        appointment_id = None

        if "_" in button_id:
            action, appointment_id = button_id.split("_", 1)
        else:
            action = button_id

        action = action.lower()
        appointment = self.appointments_db.get(appointment_id) if appointment_id else None

        if action == "confirm":
            if appointment:
                appointment.confirm()
            await self._safe_send_message(sender_phone, CONFIRMATION_MESSAGE)
            return {
                "action": "confirm",
                "appointment_id": appointment_id,
                "status": "confirmed",
                "reply_sent": CONFIRMATION_MESSAGE,
            }

        elif action == "reschedule":
            if appointment:
                appointment.confirmed_by_client = False
            await self._safe_send_message(sender_phone, RESCHEDULE_MESSAGE)
            return {
                "action": "reschedule",
                "appointment_id": appointment_id,
                "status": "rescheduled_requested",
                "reply_sent": RESCHEDULE_MESSAGE,
            }

        elif action == "cancel":
            if appointment:
                appointment.cancel(reason="Cancelled by client via WhatsApp interactive button")
                if self.calendar_provider and appointment.calendar_event_id:
                    try:
                        await self.calendar_provider.cancel_event(appointment.calendar_event_id)
                    except Exception as exc:
                        logger.error(
                            "Failed to cancel calendar event "
                            f"{appointment.calendar_event_id}: {exc}"
                        )
            await self._safe_send_message(sender_phone, CANCELLATION_MESSAGE)
            return {
                "action": "cancel",
                "appointment_id": appointment_id,
                "status": "cancelled",
                "reply_sent": CANCELLATION_MESSAGE,
            }

        logger.warning(f"Unrecognized interactive action '{action}' for button '{button_id}'")
        return {
            "action": "unknown",
            "button_id": button_id,
            "status": "unhandled",
        }

    async def _safe_send_message(self, to_phone: str, text: str) -> None:
        """Attempt to send outbound message, logging warning if credentials missing."""
        try:
            if self.wa_client and self.wa_client.access_token:
                await self.wa_client.send_text_message(to_phone, text)
        except Exception as exc:
            logger.warning(f"Could not dispatch outbound WhatsApp message to {to_phone}: {exc}")


# Global default instance
deterministic_handler = DeterministicButtonHandler()
