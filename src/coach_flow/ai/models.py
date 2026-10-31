"""Data models for AI Agent Providers, messages, and function calling."""

from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AIToolCall(BaseModel):
    """Represents a function/tool invocation request made by the AI model."""

    id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:8]}")
    function_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AIToolDefinition(BaseModel):
    """Schema definition for tools that can be invoked by the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema specification


class ChatMessage(BaseModel):
    """Normalized chat message for conversations across LLM providers."""

    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[list[AIToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class AIResponse(BaseModel):
    """Normalized model response holding generated text and/or tool calls."""

    content: Optional[str] = None
    tool_calls: list[AIToolCall] = Field(default_factory=list)
    finish_reason: Optional[str] = None

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0
