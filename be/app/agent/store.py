from typing import Protocol


class ConversationStore(Protocol):
    """Persistence boundary for conversation history.

    Agent Core depends on this interface, not a concrete implementation —
    #5 swaps NullConversationStore for a real Supabase-backed one without
    touching Agent Core.
    """

    async def get_history(self, conversation_id: str) -> list[dict]: ...

    async def append_message(
        self, conversation_id: str, role: str, content: str, model_used: str | None
    ) -> None: ...


class NullConversationStore:
    """No-op store used until #5 wires up real persistence."""

    async def get_history(self, conversation_id: str) -> list[dict]:
        return []

    async def append_message(
        self, conversation_id: str, role: str, content: str, model_used: str | None
    ) -> None:
        return None
