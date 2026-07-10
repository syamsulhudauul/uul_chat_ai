import pytest

from app.agent.core import AgentCore
from tests.test_agent_core import FakeStore, FakeToolExecutor


class FakeStreamingGatewayClient:
    """Each item in `responses` is the list of delta events for one gateway
    call, yielded in order.
    """

    def __init__(self, responses: list[list[dict]]):
        self.responses = list(responses)
        self.calls: list[tuple[list[dict], str, list[dict] | None]] = []

    async def chat_completion_stream(self, messages, model="cheap", tools=None):
        self.calls.append((list(messages), model, tools))
        for event in self.responses.pop(0):
            yield event


def _content_events(*chunks: str, finish_reason: str = "stop") -> list[dict]:
    events = [{"delta": {"content": chunk}, "finish_reason": None} for chunk in chunks]
    events.append({"delta": {}, "finish_reason": finish_reason})
    return events


def _tool_call_events(call_id: str, name: str, arguments: str = "{}") -> list[dict]:
    return [
        {
            "delta": {
                "tool_calls": [
                    {"index": 0, "id": call_id, "function": {"name": name, "arguments": ""}}
                ]
            },
            "finish_reason": None,
        },
        {
            "delta": {"tool_calls": [{"index": 0, "function": {"arguments": arguments}}]},
            "finish_reason": None,
        },
        {"delta": {}, "finish_reason": "tool_calls"},
    ]


async def _collect(agent: AgentCore, conversation_id: str, message: str) -> list[dict]:
    return [event async for event in agent.run_turn_stream(conversation_id, message)]


@pytest.mark.asyncio
async def test_run_turn_stream_yields_content_tokens_in_order():
    gateway = FakeStreamingGatewayClient(
        responses=[_content_events("Go, ", "Python, ", "and LLM agents.")]
    )
    agent = AgentCore(gateway=gateway)

    events = await _collect(agent, "conv-1", "What are your skills?")

    token_texts = [e["text"] for e in events if e["type"] == "token"]
    assert token_texts == ["Go, ", "Python, ", "and LLM agents."]

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1
    assert done_events[0]["model_used"] == "cheap"
    assert done_events[0]["text"] == "Go, Python, and LLM agents."


@pytest.mark.asyncio
async def test_run_turn_stream_does_not_yield_tokens_during_tool_resolution():
    gateway = FakeStreamingGatewayClient(
        responses=[
            _tool_call_events("call-1", "get_resume"),
            _content_events("Here's my resume summary."),
        ]
    )
    tools = FakeToolExecutor()
    agent = AgentCore(gateway=gateway, tools=tools)

    events = await _collect(agent, "conv-1", "Can I see your resume?")

    token_texts = [e["text"] for e in events if e["type"] == "token"]
    assert token_texts == ["Here's my resume summary."]
    assert tools.calls == [("get_resume", {})]

    done_events = [e for e in events if e["type"] == "done"]
    assert done_events[0]["text"] == "Here's my resume summary."

    second_call_messages = gateway.calls[1][0]
    tool_result_messages = [m for m in second_call_messages if m.get("role") == "tool"]
    assert len(tool_result_messages) == 1
    assert tool_result_messages[0]["tool_call_id"] == "call-1"


@pytest.mark.asyncio
async def test_run_turn_stream_deep_reasoning_escalates_to_strong_model():
    gateway = FakeStreamingGatewayClient(
        responses=[
            _tool_call_events("call-1", "deep_reasoning"),
            _content_events("Comparing both roles..."),
        ]
    )
    agent = AgentCore(gateway=gateway)

    events = await _collect(agent, "conv-1", "Compare your last two roles.")

    done_events = [e for e in events if e["type"] == "done"]
    assert done_events[0]["model_used"] == "strong"

    first_call_model = gateway.calls[0][1]
    second_call_model = gateway.calls[1][1]
    assert first_call_model == "cheap"
    assert second_call_model == "strong"


@pytest.mark.asyncio
async def test_run_turn_stream_persists_user_and_assistant_messages():
    gateway = FakeStreamingGatewayClient(responses=[_content_events("my reply")])
    store = FakeStore(history=[])
    agent = AgentCore(gateway=gateway, store=store)

    await _collect(agent, "conv-1", "hello")

    assert store.appended == [
        ("conv-1", "user", "hello", None),
        ("conv-1", "assistant", "my reply", "cheap"),
    ]


@pytest.mark.asyncio
async def test_run_turn_stream_unknown_tool_call_does_not_crash():
    gateway = FakeStreamingGatewayClient(
        responses=[
            _tool_call_events("call-1", "delete_everything"),
            _content_events("Sorry, I can't help with that."),
        ]
    )
    tools = FakeToolExecutor()
    agent = AgentCore(gateway=gateway, tools=tools)

    events = await _collect(agent, "conv-1", "do something weird")

    done_events = [e for e in events if e["type"] == "done"]
    assert done_events[0]["text"] == "Sorry, I can't help with that."

    second_call_messages = gateway.calls[1][0]
    tool_result_messages = [m for m in second_call_messages if m.get("role") == "tool"]
    assert "Error" in tool_result_messages[0]["content"]
