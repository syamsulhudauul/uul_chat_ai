import json

import pytest
from fastapi.testclient import TestClient

from app.agent.core import AgentCore
from app.main import app
from app.routes.chat import get_agent_core
from tests.auth_helpers import make_token


class FakeGatewayClient:
    async def chat_completion_stream(
        self, messages: list[dict], model: str = "cheap", tools: list[dict] | None = None
    ):
        yield {
            "delta": {
                "role": "assistant",
                "content": "I have experience with Go, Python, and building LLM agents.",
            },
            "finish_reason": None,
        }
        yield {"delta": {}, "finish_reason": "stop"}


@pytest.fixture(autouse=True)
def _override_agent_core():
    app.dependency_overrides[get_agent_core] = lambda: AgentCore(gateway=FakeGatewayClient())
    yield
    app.dependency_overrides.pop(get_agent_core, None)


@pytest.fixture()
def auth_header(jwks_private_key):
    token = make_token(jwks_private_key, sub="user-123", email="recruiter@example.com")
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


def _parse_sse_events(response_text: str) -> list[dict]:
    events = []
    for line in response_text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: ") :]))
    return events


def test_chat_requires_auth():
    response = client.post("/chat", json={"message": "hi"})
    assert response.status_code == 401


def test_chat_streams_tokens_and_done_event_for_authenticated_user(auth_header):
    response = client.post(
        "/chat", json={"message": "What's your experience?"}, headers=auth_header
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse_events(response.text)
    token_events = [e for e in events if e["type"] == "token"]
    done_events = [e for e in events if e["type"] == "done"]

    assert "".join(e["text"] for e in token_events) == (
        "I have experience with Go, Python, and building LLM agents."
    )
    assert len(done_events) == 1
    assert done_events[0]["model_used"] == "cheap"
    assert done_events[0]["conversation_id"]


def test_chat_reuses_provided_conversation_id(auth_header):
    response = client.post(
        "/chat",
        json={"conversation_id": "conv-abc", "message": "hi"},
        headers=auth_header,
    )
    events = _parse_sse_events(response.text)
    done_events = [e for e in events if e["type"] == "done"]
    assert done_events[0]["conversation_id"] == "conv-abc"


def test_latest_conversation_requires_auth():
    response = client.get("/conversations/latest")
    assert response.status_code == 401


def test_latest_conversation_returns_none_when_no_history(auth_header):
    response = client.get("/conversations/latest", headers=auth_header)
    assert response.status_code == 200
    assert response.json() == {"conversation_id": None, "messages": []}
