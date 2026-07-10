import json

import httpx
import pytest

from app.agent.gateway import LLMGatewayClient


def _sse_body(chunks: list[dict]) -> bytes:
    lines = [f"data: {json.dumps(chunk)}\n\n" for chunk in chunks]
    lines.append("data: [DONE]\n\n")
    return "".join(lines).encode()


def _gateway_with_handler(handler) -> LLMGatewayClient:
    gateway = LLMGatewayClient(base_url="https://example.test", api_key="test-key")
    gateway._client = httpx.AsyncClient(
        base_url="https://example.test", transport=httpx.MockTransport(handler)
    )
    return gateway


@pytest.mark.asyncio
async def test_chat_completion_stream_yields_content_deltas_in_order():
    body = _sse_body(
        [
            {"choices": [{"index": 0, "delta": {"role": "assistant", "content": "Hel"}}]},
            {"choices": [{"index": 0, "delta": {"content": "lo"}}]},
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]},
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/chat/completions"
        payload = json.loads(request.content)
        assert payload["stream"] is True
        return httpx.Response(200, content=body)

    gateway = _gateway_with_handler(handler)

    events = [
        event
        async for event in gateway.chat_completion_stream(
            [{"role": "user", "content": "hi"}], model="cheap"
        )
    ]

    assert [e["delta"].get("content") for e in events if e["delta"].get("content")] == [
        "Hel",
        "lo",
    ]
    assert events[-1]["finish_reason"] == "stop"


@pytest.mark.asyncio
async def test_chat_completion_stream_yields_tool_call_deltas():
    body = _sse_body(
        [
            {
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "call-1",
                                    "type": "function",
                                    "function": {"name": "get_resume", "arguments": ""},
                                }
                            ]
                        },
                    }
                ]
            },
            {
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [{"index": 0, "function": {"arguments": "{}"}}]
                        },
                    }
                ]
            },
            {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]},
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    gateway = _gateway_with_handler(handler)

    events = [
        event
        async for event in gateway.chat_completion_stream(
            [{"role": "user", "content": "resume?"}], model="cheap"
        )
    ]

    tool_call_events = [e for e in events if e["delta"].get("tool_calls")]
    assert len(tool_call_events) == 2
    assert tool_call_events[0]["delta"]["tool_calls"][0]["id"] == "call-1"
    assert events[-1]["finish_reason"] == "tool_calls"
