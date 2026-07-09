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
