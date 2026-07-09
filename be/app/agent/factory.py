import httpx

from app.agent.store import ConversationStore, NullConversationStore
from app.agent.supabase_store import SupabaseConversationStore
from app.config import settings


def build_conversation_store() -> ConversationStore:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return NullConversationStore()

    client = httpx.AsyncClient(
        base_url=settings.supabase_url,
        headers={
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    return SupabaseConversationStore(client)
