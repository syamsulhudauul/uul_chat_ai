from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agent.core import AgentCore
from app.agent.factory import (
    build_conversation_store,
    build_rag_retriever,
    build_tool_executor,
)
from app.agent.gateway import LLMGatewayClient
from app.agent.store import ConversationStore
from app.auth import AuthenticatedUser, verify_jwt

router = APIRouter()

_store = build_conversation_store()
_gateway = LLMGatewayClient()
_retriever = build_rag_retriever(_gateway)
_tools = build_tool_executor()
_agent = AgentCore(gateway=_gateway, store=_store, retriever=_retriever, tools=_tools)


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    model_used: str


class LatestConversationResponse(BaseModel):
    conversation_id: str | None
    messages: list[dict]


def get_agent_core() -> AgentCore:
    return _agent


def get_conversation_store() -> ConversationStore:
    return _store


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: AuthenticatedUser = Depends(verify_jwt),
    agent: AgentCore = Depends(get_agent_core),
    store: ConversationStore = Depends(get_conversation_store),
) -> ChatResponse:
    conversation_id = body.conversation_id or await store.create_conversation(
        user.user_id, "chat"
    )
    reply = await agent.run_turn(conversation_id, body.message)
    return ChatResponse(
        conversation_id=conversation_id, reply=reply.text, model_used=reply.model_used
    )


@router.get("/conversations/latest", response_model=LatestConversationResponse)
async def latest_conversation(
    user: AuthenticatedUser = Depends(verify_jwt),
    store: ConversationStore = Depends(get_conversation_store),
) -> LatestConversationResponse:
    conversation_id = await store.get_latest_conversation(user.user_id)
    if not conversation_id:
        return LatestConversationResponse(conversation_id=None, messages=[])

    messages = await store.get_history(conversation_id)
    return LatestConversationResponse(conversation_id=conversation_id, messages=messages)
