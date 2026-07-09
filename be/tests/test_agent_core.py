import pytest

from app.agent.core import AgentCore


class FakeGatewayClient:
    def __init__(self, reply: str = "Hi, I'm the AI version of syamsulhudauul."):
        self.reply = reply
        self.calls: list[tuple[list[dict], str]] = []

    async def chat(self, messages: list[dict], model: str = "cheap") -> str:
        self.calls.append((messages, model))
        return self.reply


@pytest.mark.asyncio
async def test_run_turn_returns_gateway_reply_on_cheap_tier():
    gateway = FakeGatewayClient(reply="Go, Python, and LLM agents are my core stack.")
    agent = AgentCore(gateway=gateway)

    result = await agent.run_turn("conv-1", "What are your skills?")

    assert result.text == "Go, Python, and LLM agents are my core stack."
    assert result.model_used == "cheap"


@pytest.mark.asyncio
async def test_run_turn_sends_user_message_to_gateway():
    gateway = FakeGatewayClient()
    agent = AgentCore(gateway=gateway)

    await agent.run_turn("conv-1", "What are your skills?")

    sent_messages, model = gateway.calls[0]
    assert model == "cheap"
    assert sent_messages[-1] == {"role": "user", "content": "What are your skills?"}


@pytest.mark.asyncio
async def test_run_turn_works_with_no_persistence_stub():
    gateway = FakeGatewayClient()
    agent = AgentCore(gateway=gateway)

    result = await agent.run_turn("conv-1", "hello")

    assert result.text == gateway.reply


class FakeStore:
    def __init__(self, history: list[dict]):
        self._history = history
        self.appended: list[tuple[str, str, str, str | None]] = []

    async def create_conversation(self, user_id: str, mode: str) -> str:
        return "conv-new"

    async def get_latest_conversation(self, user_id: str) -> str | None:
        return None

    async def get_history(self, conversation_id: str) -> list[dict]:
        return self._history

    async def append_message(
        self, conversation_id: str, role: str, content: str, model_used: str | None
    ) -> None:
        self.appended.append((conversation_id, role, content, model_used))


@pytest.mark.asyncio
async def test_run_turn_includes_prior_history_in_gateway_call():
    gateway = FakeGatewayClient()
    prior_history = [
        {"role": "user", "content": "What's your name?"},
        {"role": "assistant", "content": "I'm syamsulhudauul's AI."},
    ]
    store = FakeStore(history=prior_history)
    agent = AgentCore(gateway=gateway, store=store)

    await agent.run_turn("conv-1", "What are your skills?")

    sent_messages, _ = gateway.calls[0]
    assert sent_messages[0] == prior_history[0]
    assert sent_messages[1] == prior_history[1]
    assert sent_messages[-1] == {"role": "user", "content": "What are your skills?"}


@pytest.mark.asyncio
async def test_run_turn_persists_both_user_and_assistant_messages():
    gateway = FakeGatewayClient(reply="my reply")
    store = FakeStore(history=[])
    agent = AgentCore(gateway=gateway, store=store)

    await agent.run_turn("conv-1", "hello")

    assert store.appended == [
        ("conv-1", "user", "hello", None),
        ("conv-1", "assistant", "my reply", "cheap"),
    ]
