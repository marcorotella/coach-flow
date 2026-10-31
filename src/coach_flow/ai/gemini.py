"""Google Gemini API Provider."""

import logging
import os
from typing import Any, Optional

import httpx

from coach_flow.ai.base import BaseAIProvider
from coach_flow.ai.models import AIResponse, AIToolCall, AIToolDefinition, ChatMessage
from coach_flow.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """Adapter for Google Gemini GenerateContent API (supporting Gemini 1.5/2.0 Flash)."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        model = model_name or "gemini-1.5-flash"
        super().__init__(model_name=model, api_key=key)
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _format_payload(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[AIToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        system_instruction: Optional[dict[str, Any]] = None
        contents: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content or ""}]}
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content or ""}]})
            elif msg.role == "assistant":
                parts: list[dict[str, Any]] = []
                if msg.content:
                    parts.append({"text": msg.content})
                if msg.tool_calls:
                    for call in msg.tool_calls:
                        parts.append(
                            {
                                "functionCall": {
                                    "name": call.function_name,
                                    "args": call.arguments,
                                }
                            }
                        )
                if not parts:
                    parts.append({"text": ""})
                contents.append({"role": "model", "parts": parts})
            elif msg.role == "tool":
                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": msg.name or "function",
                                    "response": {
                                        "name": msg.name or "function",
                                        "content": msg.content or "",
                                    },
                                }
                            }
                        ],
                    }
                )

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }

        if system_instruction:
            payload["system_instruction"] = system_instruction

        if tools:
            declarations = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
                for tool in tools
            ]
            payload["tools"] = [{"functionDeclarations": declarations}]

        return payload

    async def generate_response(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[AIToolDefinition]] = None,
        temperature: float = 0.7,
    ) -> AIResponse:
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY.")

        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        payload = self._format_payload(messages, tools=tools, temperature=temperature)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return AIResponse(content=None, finish_reason="empty")

        candidate = candidates[0]
        content_obj = candidate.get("content", {})
        parts = content_obj.get("parts", [])

        text_content_list: list[str] = []
        tool_calls: list[AIToolCall] = []

        for part in parts:
            if "text" in part:
                text_content_list.append(part["text"])
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    AIToolCall(
                        function_name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
                    )
                )

        full_text = "\n".join(text_content_list) if text_content_list else None
        finish_reason = candidate.get("finishReason")

        return AIResponse(
            content=full_text,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )
