import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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


class LatestConversationResponse(BaseModel):
    conversation_id: str | None
    messages: list[dict]


def get_agent_core() -> AgentCore:
    return _agent


def get_conversation_store() -> ConversationStore:
    return _store


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: AuthenticatedUser = Depends(verify_jwt),
    agent: AgentCore = Depends(get_agent_core),
    store: ConversationStore = Depends(get_conversation_store),
) -> StreamingResponse:
    conversation_id = body.conversation_id or await store.create_conversation(
        user.user_id, "chat"
    )

    async def event_stream():
        async for event in agent.run_turn_stream(conversation_id, body.message):
            if event["type"] == "done":
                event = {**event, "conversation_id": conversation_id}
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations/latest", response_model=LatestConversationResponse)
async def latest_conversation(
    mode: str = "chat",
    user: AuthenticatedUser = Depends(verify_jwt),
    store: ConversationStore = Depends(get_conversation_store),
) -> LatestConversationResponse:
    conversation_id = await store.get_latest_conversation(user.user_id, mode)
    if not conversation_id:
        return LatestConversationResponse(conversation_id=None, messages=[])

    messages = await store.get_history(conversation_id)
    return LatestConversationResponse(conversation_id=conversation_id, messages=messages)
