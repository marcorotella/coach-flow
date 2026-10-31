"""Unit tests for AI Conversational Booking Agent and Tool Execution."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

from coach_flow.ai.agent import BookingAgent
from coach_flow.ai.base import BaseAIProvider
from coach_flow.ai.models import AIResponse, AIToolCall, AIToolDefinition, ChatMessage
from coach_flow.ai.tools import BookingToolExecutor
from coach_flow.calendar.mock import MockCalendarProvider
from coach_flow.config import settings
from coach_flow.main import app
from coach_flow.whatsapp.router import booking_agent


class ScriptedAIProvider(BaseAIProvider):
    """AI Provider that returns a predefined sequence of responses for testing dialog flows."""

    def __init__(self, responses: list[AIResponse]) -> None:
        super().__init__(model_name="scripted-model")
        self.responses = list(responses)
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "scripted"

    async def generate_response(
        self,
        messages: list[ChatMessage],
        tools: list[AIToolDefinition] | None = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp
        return AIResponse(content="Fine dello script di test.")


@pytest.mark.asyncio
async def test_booking_tool_executor_lifecycle():
    calendar = MockCalendarProvider(daily_start_hour=9, daily_end_hour=12)
    executor = BookingToolExecutor(calendar_provider=calendar, trainer_id="trainer-1")

    # 1. get_available_slots
    slots_json = await executor.execute(
        "get_available_slots",
        {"start_date": "2026-11-02", "end_date": "2026-11-02"},
    )
    slots_data = json.loads(slots_json)
    assert slots_data["status"] == "success"
    assert slots_data["count"] > 0

    # 2. book_appointment
    target_start = slots_data["slots"][0]["start"]
    book_json = await executor.execute(
        "book_appointment",
        {
            "start_time_iso": target_start,
            "duration_minutes": 60,
            "client_name": "Paolo Neri",
            "client_phone": "+393339998877",
            "notes": "Prima lezione conoscitiva",
        },
    )
    book_data = json.loads(book_json)
    assert book_data["status"] == "confirmed"
    event_id = book_data["calendar_event_id"]
    assert event_id.startswith("mock-cal-")
    assert len(calendar.events) == 1

    # 3. cancel_appointment
    cancel_json = await executor.execute(
        "cancel_appointment",
        {"event_id": event_id, "reason": "Imprevisto"},
    )
    cancel_data = json.loads(cancel_json)
    assert cancel_data["status"] == "cancelled"
    assert len(calendar.events) == 0

    # 4. Unknown tool
    unknown_json = await executor.execute("invalid_tool", {})
    unknown_data = json.loads(unknown_json)
    assert "error" in unknown_data


@pytest.mark.asyncio
async def test_booking_agent_tool_calling_flow():
    calendar = MockCalendarProvider(daily_start_hour=10, daily_end_hour=13)

    # Sequence:
    # 1. User: "Vorrei fissare un allenamento per il 2 novembre"
    # -> AI tool call: get_available_slots
    # 2. Agent executes tool, feeds result to AI
    # -> AI: "Ho trovato disponibilità alle 10:00 o alle 11:15. Quale preferisci?"
    # 3. User: "Preferisco le 10:00!"
    # -> AI tool call: book_appointment
    # 4. Agent executes booking tool, feeds result to AI
    # -> AI: "Perfetto! Ti ho prenotato per lunedì 2 novembre alle 10:00."

    scripted_responses = [
        # 1st step: AI requests tool get_available_slots
        AIResponse(
            tool_calls=[
                AIToolCall(
                    function_name="get_available_slots",
                    arguments={"start_date": "2026-11-02", "end_date": "2026-11-02"},
                )
            ]
        ),
        # 2nd step: AI receives tool output and proposes 2 options
        AIResponse(
            content="Ho disponibilità alle 10:00 oppure alle 11:15. Quale preferisci?"
        ),
        # 3rd step: AI requests book_appointment tool
        AIResponse(
            tool_calls=[
                AIToolCall(
                    function_name="book_appointment",
                    arguments={
                        "start_time_iso": "2026-11-02T10:00:00+00:00",
                        "client_name": "Mario Rossi",
                        "client_phone": "+393331234567",
                    },
                )
            ]
        ),
        # 4th step: AI receives booking result and confirms
        AIResponse(
            content="Ottimo Mario! La tua sessione per lunedì 2 novembre alle 10:00 è confermata!"
        ),
    ]

    ai_provider = ScriptedAIProvider(responses=scripted_responses)
    agent = BookingAgent(ai_provider=ai_provider, calendar_provider=calendar)

    # First turn
    reply1 = await agent.handle_incoming_message(
        sender_phone="+393331234567",
        user_text="Ciao! Vorrei fissare una prima sessione lunedì 2 novembre.",
        client_name="Mario Rossi",
    )
    assert "10:00" in reply1 or "11:15" in reply1

    # Second turn
    reply2 = await agent.handle_incoming_message(
        sender_phone="+393331234567",
        user_text="Perfetto, prenotiamo per le 10:00!",
        client_name="Mario Rossi",
    )
    assert "confermata" in reply2.lower()
    assert len(calendar.events) == 1


@pytest.mark.asyncio
async def test_webhook_text_message_dispatches_to_booking_agent():
    transport = ASGITransport(app=app)
    original_secret = settings.META_WA_APP_SECRET
    settings.META_WA_APP_SECRET = ""

    # Replace module-level booking_agent with mock response
    canned_reply = "Ciao! Posso aiutarti a fissare una sessione con il Coach."
    original_provider = booking_agent.ai_provider
    booking_agent.ai_provider = ScriptedAIProvider([AIResponse(content=canned_reply)])

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "999"},
                            "messages": [
                                {
                                    "id": "msg_text_1",
                                    "from": "393331112222",
                                    "timestamp": "1710000000",
                                    "type": "text",
                                    "text": {"body": "Ciao, vorrei info sui corsi"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/whatsapp/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    # Restore
    booking_agent.ai_provider = original_provider
    settings.META_WA_APP_SECRET = original_secret
