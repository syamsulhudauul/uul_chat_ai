import httpx


class KnowledgeLookup:
    """Fetches a whole source document's content back out of knowledge_chunks,
    in the order it was ingested — used by ToolExecutor for structured
    lookups (get_resume, get_project_details, get_contact_info).
    """

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def get_document(self, source_doc: str) -> str:
        response = await self._client.get(
            "/rest/v1/knowledge_chunks",
            params={
                "source_doc": f"eq.{source_doc}",
                "select": "content",
                "order": "created_at.asc",
            },
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return f"No content found for {source_doc}."
        return "\n\n".join(row["content"] for row in rows)


class NullKnowledgeLookup:
    """Used when Supabase isn't configured — keeps tools callable, just unhelpful."""

    async def get_document(self, source_doc: str) -> str:
        return f"[{source_doc} not available — knowledge base isn't configured yet]"
