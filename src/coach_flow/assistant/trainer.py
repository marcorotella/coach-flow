"""Trainer Assistant Service: Daily Digest agenda and Human Handover emergency alert."""

import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Optional

from coach_flow.config import settings
from coach_flow.domain.enums import AppointmentStatus
from coach_flow.domain.models import Appointment
from coach_flow.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

HANDOVER_PATTERNS = [
    r"\bparlare con (lui|lei|te|il coach|il personal|umano)\b",
    r"\bparlo con (il coach|te|un umano)\b",
    r"\bvoglio (un umano|un operatore|il coach)\b",
    r"\bpassami (il coach|un umano)\b",
    r"\bproblema fisico\b",
    r"\bdolore\b",
    r"\binfortunio\b",
]

HANDOVER_ACK_MESSAGE = (
    f"Certamente! Ho avvisato subito {settings.PT_NAME}, "
    "ti risponderà direttamente qui a brevissimo!"
)


class TrainerAssistantService:
    """Provides operational digests and emergency alerts directly to the Personal Trainer."""

    def __init__(
        self,
        wa_client: Optional[WhatsAppClient] = None,
        pt_phone: Optional[str] = None,
    ) -> None:
        self.wa_client = wa_client or WhatsAppClient()
        self.pt_phone = pt_phone or settings.PT_PHONE_NUMBER

    @staticmethod
    def check_handover_intent(text: str) -> bool:
        """Determines if the text contains an explicit handover or medical alert trigger."""
        lower = text.lower()
        return any(re.search(pat, lower) for pat in HANDOVER_PATTERNS)

    def generate_daily_digest(
        self,
        appointments: list[Appointment],
        target_date: Optional[date] = None,
    ) -> str:
        """Constructs formatted morning WhatsApp agenda digest."""
        day = target_date or datetime.now(timezone.utc).date()
        date_str = day.strftime("%d/%m/%Y")

        # Filter appointments for the target day
        day_appts = [
            a for a in appointments
            if a.start_time.date() == day and a.status != AppointmentStatus.CANCELLED
        ]
        day_appts.sort(key=lambda a: a.start_time)

        lines = [
            f"📋 *Buongiorno {settings.PT_NAME}!*",
            f"Ecco la tua agenda per oggi ({date_str}):\n",
        ]

        if not day_appts:
            lines.append("Nessuna sessione in programma per oggi. Buona giornata di riposo! ☕")
        else:
            for appt in day_appts:
                start_str = appt.start_time.strftime("%H:%M")
                end_str = appt.end_time.strftime("%H:%M")
                status_icon = (
                    "✅ Confermato"
                    if appt.confirmed_by_client
                    else "⏳ In attesa di conferma"
                )
                note_str = f" [Note: {appt.notes}]" if appt.notes else ""
                lines.append(
                    f"• {start_str} - {end_str}: {appt.client_id} ({status_icon}){note_str}"
                )

            lines.append(f"\nTotale sessioni oggi: *{len(day_appts)}*")
            lines.append("Buon lavoro in studio! 💪")

        return "\n".join(lines)

    async def send_daily_digest(
        self,
        appointments: list[Appointment],
        target_date: Optional[date] = None,
        pt_phone: Optional[str] = None,
    ) -> dict[str, Any]:
        """Dispatches morning agenda digest to the Personal Trainer via WhatsApp."""
        recipient = pt_phone or self.pt_phone
        digest_text = self.generate_daily_digest(appointments, target_date=target_date)

        logger.info(f"Dispatching Daily Digest to PT at {recipient}")
        result = None

        if recipient and self.wa_client.access_token:
            try:
                result = await self.wa_client.send_text_message(
                    to_phone=recipient,
                    text=digest_text,
                )
            except Exception as exc:
                logger.error(f"Failed to dispatch daily digest to PT {recipient}: {exc}")
                raise

        return {
            "status": "sent" if (result or not self.wa_client.access_token) else "failed",
            "recipient": recipient,
            "digest_text": digest_text,
        }

    async def trigger_human_handover(
        self,
        sender_phone: str,
        user_name: Optional[str] = None,
        reason: Optional[str] = None,
        pt_phone: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Sends high-priority WhatsApp alert to the Personal Trainer with direct
        one-click link to take over the client conversation.
        """
        recipient = pt_phone or self.pt_phone
        clean_phone = sender_phone.replace("+", "").replace(" ", "")
        client_display = f"{user_name} ({sender_phone})" if user_name else sender_phone
        reason_display = reason or "Richiesta esplicita cliente o domanda clinica"

        alert_message = (
            f"🚨 *ALERT SUBENTRO UMANO*\n\n"
            f"L'atleta *{client_display}* richiede assistenza diretta.\n"
            f"Motivo: {reason_display}\n\n"
            f"👉 Clicca qui per subentrare nella chat su WhatsApp:\n"
            f"https://wa.me/{clean_phone}"
        )

        logger.warning(
            f"Human Handover triggered for {client_display}. Reason: {reason_display}"
        )

        if recipient and self.wa_client.access_token:
            try:
                await self.wa_client.send_text_message(
                    to_phone=recipient,
                    text=alert_message,
                )
            except Exception as exc:
                logger.error(f"Failed to dispatch emergency handover alert to PT: {exc}")

        return {
            "status": "handover_alerted",
            "client_phone": sender_phone,
            "pt_recipient": recipient,
            "ack_message_to_client": HANDOVER_ACK_MESSAGE,
            "alert_text": alert_message,
        }
