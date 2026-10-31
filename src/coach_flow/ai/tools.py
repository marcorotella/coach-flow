"""Tools and schema declarations for AI Conversational Booking Agent."""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from coach_flow.ai.models import AIToolDefinition
from coach_flow.calendar.base import BaseCalendarProvider
from coach_flow.domain.models import Appointment

logger = logging.getLogger(__name__)

BOOKING_TOOLS: list[AIToolDefinition] = [
    AIToolDefinition(
        name="get_available_slots",
        description=(
            "Verifica gli slot orari disponibili per un allenamento tra due date "
            "(formato YYYY-MM-DD)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Data di inizio ricerca nel formato YYYY-MM-DD.",
                },
                "end_date": {
                    "type": "string",
                    "description": "Data di fine ricerca nel formato YYYY-MM-DD.",
                },
            },
            "required": ["start_date", "end_date"],
        },
    ),
    AIToolDefinition(
        name="book_appointment",
        description="Fissa un nuovo appuntamento di allenamento per il cliente.",
        parameters={
            "type": "object",
            "properties": {
                "start_time_iso": {
                    "type": "string",
                    "description": "Inizio in formato ISO 8601 (es. 2026-11-02T10:00:00Z).",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Durata della sessione in minuti (default 60).",
                },
                "client_name": {
                    "type": "string",
                    "description": "Nome del cliente.",
                },
                "client_phone": {
                    "type": "string",
                    "description": "Numero di telefono del cliente in formato E.164.",
                },
                "notes": {
                    "type": "string",
                    "description": "Note aggiuntive (obiettivi, limitazioni fisiche, ecc.).",
                },
            },
            "required": ["start_time_iso", "client_name", "client_phone"],
        },
    ),
    AIToolDefinition(
        name="cancel_appointment",
        description="Annulla un appuntamento precedentemente fissato.",
        parameters={
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Identificativo univoco dell'evento calendario.",
                },
                "reason": {
                    "type": "string",
                    "description": "Motivo dell'annullamento.",
                },
            },
            "required": ["event_id"],
        },
    ),
    AIToolDefinition(
        name="escalate_to_human",
        description="Richiede l'intervento del Coach o gestisce richieste complesse.",
        parameters={
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Motivo per cui è necessario il subentro umano.",
                },
            },
            "required": ["reason"],
        },
    ),
]


class BookingToolExecutor:
    """Executes booking tools against calendar provider and domain models."""

    def __init__(
        self,
        calendar_provider: BaseCalendarProvider,
        trainer_id: str = "default-trainer",
    ) -> None:
        self.calendar_provider = calendar_provider
        self.trainer_id = trainer_id

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Dispatch tool execution and return JSON string result."""
        try:
            if tool_name == "get_available_slots":
                return await self._get_available_slots(arguments)
            elif tool_name == "book_appointment":
                return await self._book_appointment(arguments)
            elif tool_name == "cancel_appointment":
                return await self._cancel_appointment(arguments)
            elif tool_name == "escalate_to_human":
                return json.dumps({
                    "status": "escalated",
                    "reason": arguments.get("reason", "Richiesta assistenza diretta"),
                    "note": "Il Coach è stato avvisato e subentrerà nella chat a breve.",
                })
            else:
                return json.dumps({"error": f"Tool sconosciuto '{tool_name}'"})
        except Exception as exc:
            logger.error(f"Error executing tool '{tool_name}': {exc}", exc_info=True)
            return json.dumps({"error": str(exc)})

    async def _get_available_slots(self, args: dict[str, Any]) -> str:
        start_date = date.fromisoformat(args["start_date"])
        end_date = date.fromisoformat(args["end_date"])
        slots = await self.calendar_provider.get_free_slots(
            start_date=start_date, end_date=end_date
        )
        return json.dumps(
            {
                "status": "success",
                "count": len(slots),
                "slots": [
                    {
                        "start": s.start_time.isoformat(),
                        "end": s.end_time.isoformat(),
                        "duration_minutes": s.duration_minutes,
                    }
                    for s in slots
                ],
            }
        )

    async def _book_appointment(self, args: dict[str, Any]) -> str:
        start_time = datetime.fromisoformat(args["start_time_iso"])
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        duration = int(args.get("duration_minutes", 60))
        end_time = start_time + timedelta(minutes=duration)

        client_name = args["client_name"]
        client_phone = args["client_phone"]
        notes = args.get("notes")

        app = Appointment(
            trainer_id=self.trainer_id,
            client_id=client_phone,
            start_time=start_time,
            end_time=end_time,
            notes=notes,
        )

        event_id = await self.calendar_provider.create_event(
            appointment=app,
            client_name=client_name,
            client_phone=client_phone,
            description=notes,
        )
        app.calendar_event_id = event_id

        return json.dumps(
            {
                "status": "confirmed",
                "appointment_id": app.id,
                "calendar_event_id": event_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "client_name": client_name,
            }
        )

    async def _cancel_appointment(self, args: dict[str, Any]) -> str:
        event_id = args["event_id"]
        reason = args.get("reason", "Annullato via chat")
        success = await self.calendar_provider.cancel_event(event_id)
        return json.dumps(
            {
                "status": "cancelled" if success else "failed",
                "event_id": event_id,
                "reason": reason,
            }
        )
