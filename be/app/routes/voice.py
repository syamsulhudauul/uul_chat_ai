import base64

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.agent.store import ConversationStore
from app.agent.voice import VoicePipeline
from app.auth import AuthenticatedUser, verify_jwt
from app.routes.chat import _agent, _gateway, get_conversation_store

router = APIRouter()

_voice_pipeline = VoicePipeline(gateway=_gateway, agent=_agent)


class VoiceResponse(BaseModel):
    conversation_id: str
    transcript: str
    reply: str
    model_used: str
    audio_base64: str


def get_voice_pipeline() -> VoicePipeline:
    return _voice_pipeline


@router.post("/voice", response_model=VoiceResponse)
async def voice(
    file: UploadFile = File(...),
    conversation_id: str | None = Form(None),
    user: AuthenticatedUser = Depends(verify_jwt),
    store: ConversationStore = Depends(get_conversation_store),
    pipeline: VoicePipeline = Depends(get_voice_pipeline),
) -> VoiceResponse:
    conv_id = conversation_id or await store.create_conversation(user.user_id, "voice")
    audio_bytes = await file.read()

    result = await pipeline.run_turn(conv_id, audio_bytes, filename=file.filename or "audio.webm")

    return VoiceResponse(
        conversation_id=conv_id,
        transcript=result.transcript,
        reply=result.reply.text,
        model_used=result.reply.model_used,
        audio_base64=base64.b64encode(result.audio).decode("ascii"),
    )
