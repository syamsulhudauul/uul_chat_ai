"""Re-embed knowledge/*.md into Supabase's knowledge_chunks table.

Runnable locally:
    cd be && python -m scripts.ingest

Also run automatically by .github/workflows/ingest.yml on push to main
when knowledge/ changes.
"""

import asyncio
import glob
import os

import httpx

from app.agent.chunking import chunk_markdown
from app.agent.gateway import LLMGatewayClient
from app.config import settings

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge")


def build_rest_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.supabase_url,
        headers={
            "apikey": settings.supabase_secret_key,
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "Content-Type": "application/json",
        },
        timeout=60,
    )


async def ingest_source(client: httpx.AsyncClient, gateway: LLMGatewayClient, path: str) -> int:
    source_doc = os.path.basename(path)
    with open(path, encoding="utf-8") as f:
        content = f.read()

    chunks = chunk_markdown(content, source_doc)

    # Delete-then-reinsert per source_doc keeps re-running idempotent —
    # no duplicate rows when a doc is unchanged or re-ingested.
    delete_response = await client.delete(
        "/rest/v1/knowledge_chunks", params={"source_doc": f"eq.{source_doc}"}
    )
    delete_response.raise_for_status()

    for chunk in chunks:
        embedding = await gateway.embed(chunk["content"])
        response = await client.post(
            "/rest/v1/knowledge_chunks",
            json={
                "content": chunk["content"],
                "embedding": embedding,
                "source_doc": chunk["source_doc"],
                "metadata": chunk["metadata"],
            },
        )
        response.raise_for_status()

    return len(chunks)


async def main() -> None:
    client = build_rest_client()
    gateway = LLMGatewayClient()

    paths = sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md")))
    if not paths:
        print("No knowledge files found in knowledge/.")
        return

    total = 0
    for path in paths:
        count = await ingest_source(client, gateway, path)
        print(f"Ingested {count} chunks from {os.path.basename(path)}")
        total += count

    print(f"Done. {total} chunks ingested across {len(paths)} files.")


if __name__ == "__main__":
    asyncio.run(main())
