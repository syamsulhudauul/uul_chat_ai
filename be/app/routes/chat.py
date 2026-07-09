import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.agent.core import AgentCore
from app.agent.gateway import LLMGatewayClient
from app.auth import AuthenticatedUser, verify_jwt

router = APIRouter()

_gateway = LLMGatewayClient()
_agent = AgentCore(gateway=_gateway)


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    model_used: str


def get_agent_core() -> AgentCore:
    return _agent


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: AuthenticatedUser = Depends(verify_jwt),
    agent: AgentCore = Depends(get_agent_core),
) -> ChatResponse:
    conversation_id = body.conversation_id or str(uuid.uuid4())
    reply = await agent.run_turn(conversation_id, body.message)
    return ChatResponse(
        conversation_id=conversation_id, reply=reply.text, model_used=reply.model_used
    )
