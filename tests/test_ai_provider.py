"""Unit tests for AI Agent Providers (Mock, OpenAI, and Gemini)."""

from unittest.mock import patch

import httpx
import pytest

from coach_flow.ai import (
    AIToolCall,
    AIToolDefinition,
    ChatMessage,
    GeminiProvider,
    MockAIProvider,
    OpenAIProvider,
    get_ai_provider,
)


@pytest.mark.asyncio
async def test_mock_ai_provider_text_and_tool_calls():
    provider = MockAIProvider(canned_response="Risposta di prova")
    messages = [ChatMessage(role="user", content="Ciao")]

    resp = await provider.generate_response(messages)
    assert resp.content == "Risposta di prova"
    assert resp.has_tool_calls is False
    assert len(provider.history) == 1

    # Canned tool call
    call = AIToolCall(function_name="check_slots", arguments={"date": "2026-11-02"})
    provider_tool = MockAIProvider(canned_tool_calls=[call])
    resp_tool = await provider_tool.generate_response(messages)
    assert resp_tool.has_tool_calls is True
    assert resp_tool.tool_calls[0].function_name == "check_slots"
    assert resp_tool.tool_calls[0].arguments == {"date": "2026-11-02"}


def test_openai_missing_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        provider = OpenAIProvider(api_key="")
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            provider._headers()


@pytest.mark.asyncio
async def test_openai_provider_generate_response():
    provider = OpenAIProvider(api_key="test-key", model_name="gpt-4o-mini")

    fake_openai_resp = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Ho verificato gli slot per te.",
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_available_slots",
                                "arguments": '{"date": "2026-11-02"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ]
    }

    async def mock_post(self, url, **kwargs):
        return httpx.Response(
            200,
            json=fake_openai_resp,
            request=httpx.Request("POST", url),
        )

    tools = [
        AIToolDefinition(
            name="get_available_slots",
            description="Verifica orari liberi",
            parameters={"type": "object", "properties": {"date": {"type": "string"}}},
        )
    ]
    messages = [
        ChatMessage(role="system", content="Sei un assistente PT."),
        ChatMessage(role="user", content="Quali orari hai liberi?"),
    ]

    with patch.object(httpx.AsyncClient, "post", mock_post):
        res = await provider.generate_response(messages, tools=tools)
        assert res.content == "Ho verificato gli slot per te."
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].function_name == "get_available_slots"
        assert res.tool_calls[0].arguments == {"date": "2026-11-02"}


@pytest.mark.asyncio
async def test_gemini_missing_key_raises():
    with patch.dict("os.environ", {}, clear=True):
        provider = GeminiProvider(api_key="")
        with pytest.raises(ValueError, match="Gemini API key is required"):
            await provider.generate_response([ChatMessage(role="user", content="Ciao")])


@pytest.mark.asyncio
async def test_gemini_provider_generate_response():
    provider = GeminiProvider(api_key="gemini-key", model_name="gemini-1.5-flash")

    fake_gemini_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Certo! Ecco cosa ho trovato:"},
                        {
                            "functionCall": {
                                "name": "book_appointment",
                                "args": {"slot_time": "18:00"},
                            }
                        },
                    ]
                },
                "finishReason": "STOP",
            }
        ]
    }

    async def mock_post(self, url, **kwargs):
        return httpx.Response(
            200,
            json=fake_gemini_resp,
            request=httpx.Request("POST", url),
        )

    messages = [
        ChatMessage(role="system", content="Sei un assistente PT."),
        ChatMessage(role="user", content="Voglio prenotare alle 18."),
    ]

    with patch.object(httpx.AsyncClient, "post", mock_post):
        res = await provider.generate_response(messages)
        assert res.content == "Certo! Ecco cosa ho trovato:"
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].function_name == "book_appointment"
        assert res.tool_calls[0].arguments == {"slot_time": "18:00"}


def test_ai_provider_factory():
    openai_p = get_ai_provider("openai")
    assert openai_p.provider_name == "openai"

    gemini_p = get_ai_provider("gemini")
    assert gemini_p.provider_name == "gemini"

    mock_p = get_ai_provider("mock")
    assert mock_p.provider_name == "mock"

    with pytest.raises(ValueError, match="Unsupported AI provider"):
        get_ai_provider("anthropic_unknown")
