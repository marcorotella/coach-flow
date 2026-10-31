"""Abstract Base AI Provider interface."""

from abc import ABC, abstractmethod
from typing import Optional

from coach_flow.ai.models import AIResponse, AIToolDefinition, ChatMessage


class BaseAIProvider(ABC):
    """Abstract interface defining standard capabilities for conversational AI providers."""

    def __init__(self, model_name: str, api_key: Optional[str] = None) -> None:
        self.model_name = model_name
        self.api_key = api_key

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name identifier of the provider (e.g. 'openai', 'gemini', 'mock')."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[AIToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        """
        Generate an AI completion response given message history and optional callable tools.
        """
        pass
