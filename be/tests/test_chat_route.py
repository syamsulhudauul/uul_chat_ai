import jwt
import pytest
from fastapi.testclient import TestClient

from app.agent.core import AgentCore
from app.config import settings
from app.main import app
from app.routes.chat import get_agent_core

TEST_SECRET = "test-secret"


class FakeGatewayClient:
    async def chat(self, messages: list[dict], model: str = "cheap") -> str:
        return "I have experience with Go, Python, and building LLM agents."


@pytest.fixture(autouse=True)
def _set_jwt_secret(monkeypatch):
    monkeypatch.setattr(settings, "supabase_jwt_secret", TEST_SECRET)


@pytest.fixture(autouse=True)
def _override_agent_core():
    app.dependency_overrides[get_agent_core] = lambda: AgentCore(gateway=FakeGatewayClient())
    yield
    app.dependency_overrides.pop(get_agent_core, None)


client = TestClient(app)


def _auth_header():
    token = jwt.encode(
        {"sub": "user-123", "email": "recruiter@example.com", "aud": "authenticated"},
        TEST_SECRET,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_chat_requires_auth():
    response = client.post("/chat", json={"message": "hi"})
    assert response.status_code == 401


def test_chat_returns_reply_for_authenticated_user():
    response = client.post("/chat", json={"message": "What's your experience?"}, headers=_auth_header())
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "I have experience with Go, Python, and building LLM agents."
    assert body["model_used"] == "cheap"
    assert body["conversation_id"]


def test_chat_reuses_provided_conversation_id():
    response = client.post(
        "/chat",
        json={"conversation_id": "conv-abc", "message": "hi"},
        headers=_auth_header(),
    )
    assert response.json()["conversation_id"] == "conv-abc"


def test_latest_conversation_requires_auth():
    response = client.get("/conversations/latest")
    assert response.status_code == 401


def test_latest_conversation_returns_none_when_no_history():
    response = client.get("/conversations/latest", headers=_auth_header())
    assert response.status_code == 200
    assert response.json() == {"conversation_id": None, "messages": []}
