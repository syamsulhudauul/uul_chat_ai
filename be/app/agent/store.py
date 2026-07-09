import uuid
from typing import Protocol


class ConversationStore(Protocol):
    """Persistence boundary for conversation history.

    Agent Core depends on this interface, not a concrete implementation —
    SupabaseConversationStore (real persistence) and NullConversationStore
    (no-op) are interchangeable behind it.
    """

    async def create_conversation(self, user_id: str, mode: str) -> str: ...

    async def get_latest_conversation(self, user_id: str) -> str | None: ...

    async def get_history(self, conversation_id: str) -> list[dict]: ...

    async def append_message(
        self, conversation_id: str, role: str, content: str, model_used: str | None
    ) -> None: ...


class NullConversationStore:
    """No-op store used when Supabase isn't configured (e.g. local dev without secrets)."""

    async def create_conversation(self, user_id: str, mode: str) -> str:
        return str(uuid.uuid4())

    async def get_latest_conversation(self, user_id: str) -> str | None:
        return None

    async def get_history(self, conversation_id: str) -> list[dict]:
        return []

    async def append_message(
        self, conversation_id: str, role: str, content: str, model_used: str | None
    ) -> None:
        return None
