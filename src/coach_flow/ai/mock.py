"""In-memory Mock AI Provider for offline simulation and deterministic testing."""

from typing import Optional

from coach_flow.ai.base import BaseAIProvider
from coach_flow.ai.models import AIResponse, AIToolCall, AIToolDefinition, ChatMessage


class MockAIProvider(BaseAIProvider):
    """Simulates AI model behavior without external network calls."""

    def __init__(
        self,
        model_name: str = "mock-model",
        canned_response: Optional[str] = None,
        canned_tool_calls: Optional[list[AIToolCall]] = None,
    ) -> None:
        super().__init__(model_name=model_name, api_key="mock-key")
        self.canned_response = canned_response
        self.canned_tool_calls = canned_tool_calls or []
        self.history: list[list[ChatMessage]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate_response(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[AIToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        self.history.append(messages)

        if self.canned_tool_calls:
            calls = list(self.canned_tool_calls)
            return AIResponse(
                content=self.canned_response,
                tool_calls=calls,
                finish_reason="tool_calls",
            )

        content = (
            self.canned_response
            if self.canned_response is not None
            else "Certamente! Posso aiutarti a verificare gli slot e prenotare la sessione."
        )
        return AIResponse(content=content, finish_reason="stop")
