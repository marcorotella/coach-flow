"""AI Conversational Booking Agent for Personal Trainers."""

import logging
from typing import Optional

from coach_flow.ai.base import BaseAIProvider
from coach_flow.ai.models import ChatMessage
from coach_flow.ai.tools import BOOKING_TOOLS, BookingToolExecutor
from coach_flow.calendar.base import BaseCalendarProvider
from coach_flow.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""Sei l'assistente virtuale ufficiale del Personal Trainer {settings.PT_NAME}.
Il tuo compito principale è aiutare lead e clienti su WhatsApp a:
1. Conoscere i percorsi di allenamento e rispondere cordialmente alle loro domande.
2. Concordare e fissare sessioni verificando la reale disponibilità nel calendario.
3. Proporre sempre 2 opzioni orarie concrete (es. "Giovedì alle 18:30 o venerdì alle 17:30?").
4. Quando l'atleta sceglie uno slot, invoca autonomamente lo strumento `book_appointment`.
5. Sii empatico, motivante, professionale e conciso (stile WhatsApp). Rispondi in italiano.
"""


class BookingAgent:
    """Manages multi-turn booking dialogues with function calling and memory."""

    def __init__(
        self,
        ai_provider: BaseAIProvider,
        calendar_provider: BaseCalendarProvider,
        system_prompt: str = SYSTEM_PROMPT,
        max_tool_iterations: int = 5,
    ) -> None:
        self.ai_provider = ai_provider
        self.calendar_provider = calendar_provider
        self.system_prompt = system_prompt
        self.max_tool_iterations = max_tool_iterations
        self.tool_executor = BookingToolExecutor(calendar_provider=calendar_provider)
        self.sessions: dict[str, list[ChatMessage]] = {}

    def get_session_history(self, session_id: str) -> list[ChatMessage]:
        """Retrieve or initialize conversation history for a phone number."""
        if session_id not in self.sessions:
            self.sessions[session_id] = [
                ChatMessage(role="system", content=self.system_prompt)
            ]
        return self.sessions[session_id]

    async def handle_incoming_message(
        self,
        sender_phone: str,
        user_text: str,
        client_name: Optional[str] = None,
    ) -> str:
        """
        Process incoming text from WhatsApp, execute tools if required,
        and return final natural language assistant response.
        """
        history = self.get_session_history(sender_phone)
        history.append(ChatMessage(role="user", content=user_text))

        iterations = 0
        while iterations < self.max_tool_iterations:
            iterations += 1
            response = await self.ai_provider.generate_response(
                messages=history,
                tools=BOOKING_TOOLS,
            )

            if response.has_tool_calls:
                # Add assistant message with tool calls to history
                history.append(
                    ChatMessage(
                        role="assistant",
                        content=response.content,
                        tool_calls=response.tool_calls,
                    )
                )

                # Execute each tool call
                for call in response.tool_calls:
                    logger.info(
                        f"Executing tool {call.function_name} with args {call.arguments}"
                    )
                    # Automatically inject client_phone if missing
                    if "client_phone" in call.arguments and not call.arguments["client_phone"]:
                        call.arguments["client_phone"] = sender_phone
                    if "client_name" in call.arguments and not call.arguments["client_name"]:
                        call.arguments["client_name"] = client_name or "Cliente"

                    tool_output = await self.tool_executor.execute(
                        tool_name=call.function_name,
                        arguments=call.arguments,
                    )

                    history.append(
                        ChatMessage(
                            role="tool",
                            tool_call_id=call.id,
                            name=call.function_name,
                            content=tool_output,
                        )
                    )
                # Continue loop to let LLM formulate conversational response
                continue

            # Final assistant response without tool calls
            final_text = response.content or "Sono a tua disposizione per qualsiasi informazione!"
            history.append(ChatMessage(role="assistant", content=final_text))
            return final_text

        return "Ho registrato la tua richiesta e verificherò subito con il coach!"
