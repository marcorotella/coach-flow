"""AI layer exports and provider factory."""

from typing import Optional

from coach_flow.ai.base import BaseAIProvider
from coach_flow.ai.gemini import GeminiProvider
from coach_flow.ai.mock import MockAIProvider
from coach_flow.ai.models import AIResponse, AIToolCall, AIToolDefinition, ChatMessage
from coach_flow.ai.openai import OpenAIProvider
from coach_flow.config import settings


def get_ai_provider(provider_type: Optional[str] = None) -> BaseAIProvider:
    """Factory creating configured AI Provider instance."""
    prov = (provider_type or settings.AI_PROVIDER).lower()

    if prov == "gemini":
        return GeminiProvider()
    elif prov == "openai":
        return OpenAIProvider()
    elif prov == "mock":
        return MockAIProvider()
    else:
        raise ValueError(
            f"Unsupported AI provider: '{prov}'. Choose 'openai', 'gemini', or 'mock'."
        )


__all__ = [
    "BaseAIProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "MockAIProvider",
    "ChatMessage",
    "AIToolDefinition",
    "AIToolCall",
    "AIResponse",
    "get_ai_provider",
]
