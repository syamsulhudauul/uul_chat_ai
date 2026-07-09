import httpx
import pytest

from app.agent.supabase_store import SupabaseConversationStore


def _store_with_handler(handler):
    client = httpx.AsyncClient(
        base_url="https://example.supabase.co", transport=httpx.MockTransport(handler)
    )
    return SupabaseConversationStore(client)


@pytest.mark.asyncio
async def test_create_conversation_returns_new_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/v1/conversations"
        assert request.method == "POST"
        return httpx.Response(201, json=[{"id": "conv-1"}])

    store = _store_with_handler(handler)
    conversation_id = await store.create_conversation("user-1", "chat")

    assert conversation_id == "conv-1"


@pytest.mark.asyncio
async def test_get_latest_conversation_returns_none_when_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    store = _store_with_handler(handler)
    result = await store.get_latest_conversation("user-1")

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_conversation_returns_most_recent_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "user_id=eq.user-1" in str(request.url)
        return httpx.Response(200, json=[{"id": "conv-42"}])

    store = _store_with_handler(handler)
    result = await store.get_latest_conversation("user-1")

    assert result == "conv-42"


@pytest.mark.asyncio
async def test_get_history_returns_rows_in_order():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "order=created_at.asc" in str(request.url)
        return httpx.Response(
            200,
            json=[
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
        )

    store = _store_with_handler(handler)
    history = await store.get_history("conv-1")

    assert history == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]


@pytest.mark.asyncio
async def test_append_message_posts_expected_row():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read()
        return httpx.Response(201, json=[{}])

    store = _store_with_handler(handler)
    await store.append_message("conv-1", "assistant", "hello", "cheap")

    body = captured["body"]
    assert b"assistant" in body
    assert b"hello" in body
    assert b"cheap" in body
