from dataclasses import dataclass
from typing import Protocol

from app.agent.gateway import LLMGatewayClient
from app.agent.store import ConversationStore, NullConversationStore

GROUNDING_INSTRUCTIONS = (
    "You are the AI representative of syamsulhudauul, an Applied AI Engineer. "
    "Answer using only the following grounding context about him. "
    "If the answer isn't covered by the context, say you don't have that "
    "information rather than guessing."
)


@dataclass
class AgentReply:
    text: str
    model_used: str


class Retriever(Protocol):
    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]: ...


class AgentCore:
    """Transport-agnostic reasoning core — chat and voice both call run_turn().

    Tool-calling and model-tier escalation are added in later issues
    (#7, #8) without changing this interface.
    """

    def __init__(
        self,
        gateway: LLMGatewayClient,
        store: ConversationStore | None = None,
        retriever: Retriever | None = None,
    ):
        self.gateway = gateway
        self.store = store or NullConversationStore()
        self.retriever = retriever

    async def run_turn(self, conversation_id: str, user_message: str) -> AgentReply:
        history = await self.store.get_history(conversation_id)
        messages = list(history)

        if self.retriever is not None:
            chunks = await self.retriever.retrieve(user_message)
            if chunks:
                context = "\n\n".join(
                    f"[{chunk['source_doc']}] {chunk['content']}" for chunk in chunks
                )
                messages.insert(
                    0, {"role": "system", "content": f"{GROUNDING_INSTRUCTIONS}\n\n{context}"}
                )

        messages.append({"role": "user", "content": user_message})

        model = "cheap"
        reply_text = await self.gateway.chat(messages, model=model)

        await self.store.append_message(conversation_id, "user", user_message, None)
        await self.store.append_message(conversation_id, "assistant", reply_text, model)

        return AgentReply(text=reply_text, model_used=model)
