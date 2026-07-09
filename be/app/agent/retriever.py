import httpx

from app.agent.gateway import LLMGatewayClient


class RAGRetriever:
    """Embeds a query and finds the closest knowledge_chunks via the
    match_knowledge_chunks Postgres function (pgvector cosine distance),
    called through Supabase's PostgREST RPC endpoint.
    """

    def __init__(self, gateway: LLMGatewayClient, client: httpx.AsyncClient):
        self.gateway = gateway
        self._client = client

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = await self.gateway.embed(query)
        response = await self._client.post(
            "/rest/v1/rpc/match_knowledge_chunks",
            json={"query_embedding": embedding, "match_count": top_k},
        )
        response.raise_for_status()
        return response.json()
