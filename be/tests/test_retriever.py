import httpx
import pytest

from app.agent.retriever import RAGRetriever


class FakeGateway:
    def __init__(self):
        self.embedded_queries: list[str] = []

    async def embed(self, text: str, model: str = "embeddings") -> list[float]:
        self.embedded_queries.append(text)
        return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_retrieve_calls_match_rpc_with_query_embedding():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json=[
                {
                    "id": "c1",
                    "content": "Go, Python, and LLM agents.",
                    "source_doc": "skills.md",
                    "metadata": {},
                    "similarity": 0.9,
                }
            ],
        )

    client = httpx.AsyncClient(
        base_url="https://example.supabase.co", transport=httpx.MockTransport(handler)
    )
    gateway = FakeGateway()
    retriever = RAGRetriever(gateway, client)

    chunks = await retriever.retrieve("What are your skills?", top_k=5)

    assert captured["path"] == "/rest/v1/rpc/match_knowledge_chunks"
    assert b"match_count" in captured["body"]
    assert chunks[0]["content"] == "Go, Python, and LLM agents."
    assert gateway.embedded_queries == ["What are your skills?"]


@pytest.mark.asyncio
async def test_retrieve_returns_empty_list_when_no_matches():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = httpx.AsyncClient(
        base_url="https://example.supabase.co", transport=httpx.MockTransport(handler)
    )
    retriever = RAGRetriever(FakeGateway(), client)

    chunks = await retriever.retrieve("irrelevant question")

    assert chunks == []
