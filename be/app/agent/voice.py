from dataclasses import dataclass

from app.agent.core import AgentCore, AgentReply
from app.agent.gateway import LLMGatewayClient


@dataclass
class VoiceReply:
    transcript: str
    reply: AgentReply
    audio: bytes


class VoicePipeline:
    """Thin orchestration over Agent Core — no reasoning logic of its own.

    Raw audio is only ever held in memory for the duration of this call;
    it's never written to disk or storage, only the transcript is
    persisted (by Agent Core, via the normal message-append path).
    """

    def __init__(self, gateway: LLMGatewayClient, agent: AgentCore):
        self.gateway = gateway
        self.agent = agent

    async def run_turn(
        self, conversation_id: str, audio_bytes: bytes, filename: str = "audio.webm"
    ) -> VoiceReply:
        transcript = await self.gateway.transcribe(audio_bytes, filename=filename)
        reply = await self.agent.run_turn(conversation_id, transcript)
        audio = await self.gateway.speak(reply.text)
        return VoiceReply(transcript=transcript, reply=reply, audio=audio)
