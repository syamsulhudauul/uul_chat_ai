import httpx

from app.agent.gateway import LLMGatewayClient
from app.agent.knowledge import KnowledgeLookup, NullKnowledgeLookup
from app.agent.retriever import RAGRetriever
from app.agent.store import ConversationStore, NullConversationStore
from app.agent.supabase_store import SupabaseConversationStore
from app.agent.tools import ToolExecutor
from app.config import settings


def _supabase_configured() -> bool:
    return bool(settings.supabase_url and settings.supabase_secret_key)


def _supabase_rest_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.supabase_url,
        headers={
            "apikey": settings.supabase_secret_key,
            "Authorization": f"Bearer {settings.supabase_secret_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )


def build_conversation_store() -> ConversationStore:
    if not _supabase_configured():
        return NullConversationStore()
    return SupabaseConversationStore(_supabase_rest_client())


def build_rag_retriever(gateway: LLMGatewayClient) -> RAGRetriever | None:
    if not _supabase_configured():
        return None
    return RAGRetriever(gateway, _supabase_rest_client())


def build_tool_executor() -> ToolExecutor:
    knowledge = (
        KnowledgeLookup(_supabase_rest_client())
        if _supabase_configured()
        else NullKnowledgeLookup()
    )
    return ToolExecutor(knowledge)
