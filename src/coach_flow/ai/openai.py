"""OpenAI Chat Completions API Provider."""

import json
import logging
import os
from typing import Any, Optional

import httpx

from coach_flow.ai.base import BaseAIProvider
from coach_flow.ai.models import AIResponse, AIToolCall, AIToolDefinition, ChatMessage
from coach_flow.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """Adapter for OpenAI Chat Completions API (supporting GPT-4o-mini, etc.)."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
    ) -> None:
        key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        model = model_name or settings.AI_MODEL_NAME or "gpt-4o-mini"
        super().__init__(model_name=model, api_key=key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "openai"

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _format_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        formatted: list[dict[str, Any]] = []
        for msg in messages:
            entry: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                entry["content"] = msg.content
            if msg.role == "tool" and msg.tool_call_id:
                entry["tool_call_id"] = msg.tool_call_id
                if msg.name:
                    entry["name"] = msg.name
            if msg.role == "assistant" and msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function_name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in msg.tool_calls
                ]
            formatted.append(entry)
        return formatted

    def _format_tools(self, tools: list[AIToolDefinition]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in tools
        ]

    async def generate_response(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[AIToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": self._format_messages(messages),
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = self._format_tools(tools)
            payload["tool_choice"] = "auto"

        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        choice_msg = choice.get("message", {})
        raw_tool_calls = choice_msg.get("tool_calls", [])

        parsed_tool_calls: list[AIToolCall] = []
        for tc in raw_tool_calls:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except Exception:
                args = {}
            parsed_tool_calls.append(
                AIToolCall(
                    id=tc.get("id", ""),
                    function_name=fn.get("name", ""),
                    arguments=args,
                )
            )

        return AIResponse(
            content=choice_msg.get("content"),
            tool_calls=parsed_tool_calls,
            finish_reason=choice.get("finish_reason"),
        )
