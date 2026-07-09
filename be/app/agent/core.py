from dataclasses import dataclass

from app.agent.gateway import LLMGatewayClient
from app.agent.store import ConversationStore, NullConversationStore


@dataclass
class AgentReply:
    text: str
    model_used: str


class AgentCore:
    """Transport-agnostic reasoning core — chat and voice both call run_turn().

    RAG retrieval, tool-calling, and model-tier escalation are added in
    later issues (#6, #7, #8) without changing this interface.
    """

    def __init__(self, gateway: LLMGatewayClient, store: ConversationStore | None = None):
        self.gateway = gateway
        self.store = store or NullConversationStore()

    async def run_turn(self, conversation_id: str, user_message: str) -> AgentReply:
        history = await self.store.get_history(conversation_id)
        messages = [*history, {"role": "user", "content": user_message}]

        model = "cheap"
        reply_text = await self.gateway.chat(messages, model=model)

        await self.store.append_message(conversation_id, "user", user_message, None)
        await self.store.append_message(conversation_id, "assistant", reply_text, model)

        return AgentReply(text=reply_text, model_used=model)
