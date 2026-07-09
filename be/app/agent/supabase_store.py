import httpx


class SupabaseConversationStore:
    """ConversationStore backed by Supabase's PostgREST API.

    Takes an already-configured httpx.AsyncClient (base_url + service-role
    auth headers) so it stays trivially testable with httpx.MockTransport.
    """

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def create_conversation(self, user_id: str, mode: str) -> str:
        response = await self._client.post(
            "/rest/v1/conversations",
            json={"user_id": user_id, "mode": mode},
            headers={"Prefer": "return=representation"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0]["id"]

    async def get_latest_conversation(self, user_id: str, mode: str) -> str | None:
        response = await self._client.get(
            "/rest/v1/conversations",
            params={
                "user_id": f"eq.{user_id}",
                "mode": f"eq.{mode}",
                "select": "id",
                "order": "created_at.desc",
                "limit": "1",
            },
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0]["id"] if rows else None

    async def get_history(self, conversation_id: str) -> list[dict]:
        response = await self._client.get(
            "/rest/v1/messages",
            params={
                "conversation_id": f"eq.{conversation_id}",
                "select": "role,content",
                "order": "created_at.asc",
            },
        )
        response.raise_for_status()
        return response.json()

    async def append_message(
        self, conversation_id: str, role: str, content: str, model_used: str | None
    ) -> None:
        response = await self._client.post(
            "/rest/v1/messages",
            json={
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "model_used": model_used,
            },
        )
        response.raise_for_status()
