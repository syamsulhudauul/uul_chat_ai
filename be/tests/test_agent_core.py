import pytest

from app.agent.core import AgentCore


class FakeGatewayClient:
    """Returns queued responses in order (one per gateway call), or a fixed
    single-turn reply if no queue was given.
    """

    def __init__(self, responses=None, reply: str = "Hi, I'm the AI version of syamsulhudauul."):
        self.responses = list(responses) if responses is not None else None
        self.reply = reply
        self.calls: list[tuple[list[dict], str, list[dict] | None]] = []

    async def chat_completion(
        self, messages: list[dict], model: str = "cheap", tools: list[dict] | None = None
    ) -> dict:
        self.calls.append((list(messages), model, tools))
        if self.responses is not None:
            return self.responses.pop(0)
        return {"role": "assistant", "content": self.reply, "tool_calls": None}


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

    sent_messages, model, _tools = gateway.calls[0]
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

    sent_messages, _model, _tools = gateway.calls[0]
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


class FakeRetriever:
    def __init__(self, chunks: list[dict]):
        self._chunks = chunks
        self.queried: list[str] = []

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        self.queried.append(query)
        return self._chunks


@pytest.mark.asyncio
async def test_run_turn_grounds_reply_with_retrieved_chunks():
    gateway = FakeGatewayClient()
    retriever = FakeRetriever(
        [{"source_doc": "skills.md", "content": "Go, Python, and LLM agents."}]
    )
    agent = AgentCore(gateway=gateway, retriever=retriever)

    await agent.run_turn("conv-1", "What are your skills?")

    sent_messages, _model, _tools = gateway.calls[0]
    assert sent_messages[0]["role"] == "system"
    assert "Go, Python, and LLM agents." in sent_messages[0]["content"]
    assert sent_messages[-1] == {"role": "user", "content": "What are your skills?"}
    assert retriever.queried == ["What are your skills?"]


@pytest.mark.asyncio
async def test_run_turn_without_retriever_has_no_system_message():
    gateway = FakeGatewayClient()
    agent = AgentCore(gateway=gateway)

    await agent.run_turn("conv-1", "hi")

    sent_messages, _model, _tools = gateway.calls[0]
    assert all(message["role"] != "system" for message in sent_messages)


@pytest.mark.asyncio
async def test_run_turn_with_retriever_but_no_matches_has_no_system_message():
    gateway = FakeGatewayClient()
    retriever = FakeRetriever([])
    agent = AgentCore(gateway=gateway, retriever=retriever)

    await agent.run_turn("conv-1", "hi")

    sent_messages, _model, _tools = gateway.calls[0]
    assert all(message["role"] != "system" for message in sent_messages)


class FakeToolExecutor:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def list_tools(self) -> list[dict]:
        return [{"type": "function", "function": {"name": "get_resume", "parameters": {}}}]

    async def execute(self, tool_name: str, args: dict) -> str:
        self.calls.append((tool_name, args))
        if tool_name != "get_resume":
            raise ValueError(f"Unknown tool: {tool_name}")
        return "Resume: Applied AI Engineer with a focus on LLM agents."


def _tool_call_response(call_id: str, name: str, arguments: str = "{}") -> dict:
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": call_id, "function": {"name": name, "arguments": arguments}}],
    }


@pytest.mark.asyncio
async def test_run_turn_executes_tool_call_and_resolves_with_second_response():
    gateway = FakeGatewayClient(
        responses=[
            _tool_call_response("call-1", "get_resume"),
            {
                "role": "assistant",
                "content": "Here's a summary of my resume.",
                "tool_calls": None,
            },
        ]
    )
    tools = FakeToolExecutor()
    agent = AgentCore(gateway=gateway, tools=tools)

    result = await agent.run_turn("conv-1", "Can I see your resume?")

    assert result.text == "Here's a summary of my resume."
    assert tools.calls == [("get_resume", {})]

    second_call_messages, _model, _tools_schema = gateway.calls[1]
    tool_result_messages = [m for m in second_call_messages if m.get("role") == "tool"]
    assert len(tool_result_messages) == 1
    assert tool_result_messages[0]["tool_call_id"] == "call-1"
    assert "Applied AI Engineer" in tool_result_messages[0]["content"]


@pytest.mark.asyncio
async def test_run_turn_unknown_tool_call_does_not_crash():
    gateway = FakeGatewayClient(
        responses=[
            _tool_call_response("call-1", "delete_everything"),
            {"role": "assistant", "content": "Sorry, I can't help with that.", "tool_calls": None},
        ]
    )
    tools = FakeToolExecutor()
    agent = AgentCore(gateway=gateway, tools=tools)

    result = await agent.run_turn("conv-1", "do something weird")

    assert result.text == "Sorry, I can't help with that."
    second_call_messages, _model, _tools_schema = gateway.calls[1]
    tool_result_messages = [m for m in second_call_messages if m.get("role") == "tool"]
    assert "Error" in tool_result_messages[0]["content"]


@pytest.mark.asyncio
async def test_run_turn_tool_call_without_tool_executor_returns_error_result():
    gateway = FakeGatewayClient(
        responses=[
            _tool_call_response("call-1", "get_resume"),
            {"role": "assistant", "content": "Fallback reply.", "tool_calls": None},
        ]
    )
    agent = AgentCore(gateway=gateway, tools=None)

    result = await agent.run_turn("conv-1", "Can I see your resume?")

    assert result.text == "Fallback reply."
    second_call_messages, _model, _tools_schema = gateway.calls[1]
    tool_result_messages = [m for m in second_call_messages if m.get("role") == "tool"]
    assert "Error" in tool_result_messages[0]["content"]
