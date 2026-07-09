import httpx
import pytest

from scripts.ingest import ingest_source


class FakeGateway:
    async def embed(self, text: str, model: str = "embeddings") -> list[float]:
        return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_ingest_source_deletes_before_reinserting(tmp_path):
    doc = tmp_path / "resume.md"
    doc.write_text("## Summary\n\nApplied AI Engineer.\n")

    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(201, json=[{}])

    client = httpx.AsyncClient(
        base_url="https://example.supabase.co", transport=httpx.MockTransport(handler)
    )

    count = await ingest_source(client, FakeGateway(), str(doc))

    assert count == 1
    methods = [call[0] for call in calls]
    assert methods[0] == "DELETE"
    assert methods[1] == "POST"


@pytest.mark.asyncio
async def test_ingest_source_running_twice_does_not_accumulate_rows(tmp_path):
    doc = tmp_path / "skills.md"
    doc.write_text("## Languages\n\nGo, Python.\n")

    deletes = 0
    posts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal deletes, posts
        if request.method == "DELETE":
            deletes += 1
            return httpx.Response(204)
        posts += 1
        return httpx.Response(201, json=[{}])

    client = httpx.AsyncClient(
        base_url="https://example.supabase.co", transport=httpx.MockTransport(handler)
    )
    gateway = FakeGateway()

    await ingest_source(client, gateway, str(doc))
    await ingest_source(client, gateway, str(doc))

    # One chunk in this doc: each run must delete first, so two runs
    # produce 2 deletes / 2 posts, never accumulating past 1 chunk's worth
    # of rows per run.
    assert deletes == 2
    assert posts == 2


@pytest.mark.asyncio
async def test_ingest_source_embeds_and_upserts_every_chunk(tmp_path):
    doc = tmp_path / "faq.md"
    doc.write_text("## Q1\n\nAnswer 1.\n\n## Q2\n\nAnswer 2.\n")

    posted_bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            posted_bodies.append(request.read())
        return httpx.Response(204 if request.method == "DELETE" else 201, json=[{}])

    client = httpx.AsyncClient(
        base_url="https://example.supabase.co", transport=httpx.MockTransport(handler)
    )

    count = await ingest_source(client, FakeGateway(), str(doc))

    assert count == 2
    assert len(posted_bodies) == 2
    assert b"Answer 1" in posted_bodies[0]
    assert b"Answer 2" in posted_bodies[1]
