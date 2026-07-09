import base64

import pytest
from fastapi.testclient import TestClient

from app.agent.core import AgentReply
from app.agent.voice import VoiceReply
from app.main import app
from app.routes.voice import get_voice_pipeline
from tests.auth_helpers import make_token


class FakeStore:
    def __init__(self):
        self.created: list[tuple[str, str]] = []

    async def create_conversation(self, user_id: str, mode: str) -> str:
        self.created.append((user_id, mode))
        return "conv-voice-1"

    async def get_latest_conversation(self, user_id: str, mode: str) -> str | None:
        return None

    async def get_history(self, conversation_id: str) -> list[dict]:
        return []

    async def append_message(self, conversation_id, role, content, model_used) -> None:
        return None


class FakeVoicePipeline:
    async def run_turn(self, conversation_id: str, audio_bytes: bytes):
        return VoiceReply(
            transcript="What are your skills?",
            reply=AgentReply(text="Go, Python, and LLM agents.", model_used="cheap"),
            audio=b"fake-mp3-bytes",
        )


@pytest.fixture()
def fake_store():
    return FakeStore()


@pytest.fixture(autouse=True)
def _override_dependencies(fake_store):
    from app.routes.chat import get_conversation_store

    app.dependency_overrides[get_conversation_store] = lambda: fake_store
    app.dependency_overrides[get_voice_pipeline] = lambda: FakeVoicePipeline()
    yield
    app.dependency_overrides.pop(get_conversation_store, None)
    app.dependency_overrides.pop(get_voice_pipeline, None)


@pytest.fixture()
def auth_header(jwks_private_key):
    token = make_token(jwks_private_key, sub="user-123", email="recruiter@example.com")
    return {"Authorization": f"Bearer {token}"}


client = TestClient(app)


def test_voice_requires_auth():
    response = client.post("/voice", files={"file": ("recording.webm", b"audio", "audio/webm")})
    assert response.status_code == 401


def test_voice_returns_transcript_reply_and_audio(fake_store, auth_header):
    response = client.post(
        "/voice",
        files={"file": ("recording.webm", b"audio-bytes", "audio/webm")},
        headers=auth_header,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["transcript"] == "What are your skills?"
    assert body["reply"] == "Go, Python, and LLM agents."
    assert body["model_used"] == "cheap"
    assert base64.b64decode(body["audio_base64"]) == b"fake-mp3-bytes"


def test_voice_creates_a_voice_mode_conversation_when_none_provided(fake_store, auth_header):
    client.post(
        "/voice",
        files={"file": ("recording.webm", b"audio-bytes", "audio/webm")},
        headers=auth_header,
    )

    assert fake_store.created == [("user-123", "voice")]


def test_voice_reuses_provided_conversation_id(fake_store, auth_header):
    response = client.post(
        "/voice",
        files={"file": ("recording.webm", b"audio-bytes", "audio/webm")},
        data={"conversation_id": "conv-existing"},
        headers=auth_header,
    )

    assert response.json()["conversation_id"] == "conv-existing"
    assert fake_store.created == []
