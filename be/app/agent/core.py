import json
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

MAX_TOOL_ITERATIONS = 3

DEEP_REASONING_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "deep_reasoning",
        "description": (
            "Use for synthesis or comparison questions that need careful reasoning "
            "across multiple pieces of context (e.g. comparing experience across two "
            "roles), rather than a simple factual lookup. Switches to a stronger model "
            "for the rest of this turn."
        ),
        "parameters": {"type": "object", "properties": {}},
    },
}


@dataclass
class AgentReply:
    text: str
    model_used: str


class Retriever(Protocol):
    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]: ...


class ToolExecutorProtocol(Protocol):
    def list_tools(self) -> list[dict]: ...

    async def execute(self, tool_name: str, args: dict) -> str: ...


class AgentCore:
    """Transport-agnostic reasoning core — chat and voice both call run_turn()."""

    def __init__(
        self,
        gateway: LLMGatewayClient,
        store: ConversationStore | None = None,
        retriever: Retriever | None = None,
        tools: ToolExecutorProtocol | None = None,
    ):
        self.gateway = gateway
        self.store = store or NullConversationStore()
        self.retriever = retriever
        self.tools = tools

    async def run_turn(self, conversation_id: str, user_message: str) -> AgentReply:
        history = await self.store.get_history(conversation_id)
        messages = list(history)

        if self.retriever is not None:
            try:
                chunks = await self.retriever.retrieve(user_message)
            except Exception:
                # A flaky/misconfigured embeddings provider shouldn't 500 the
                # whole turn — degrade to an ungrounded reply instead.
                chunks = []
            if chunks:
                context = "\n\n".join(
                    f"[{chunk['source_doc']}] {chunk['content']}" for chunk in chunks
                )
                messages.insert(
                    0, {"role": "system", "content": f"{GROUNDING_INSTRUCTIONS}\n\n{context}"}
                )

        messages.append({"role": "user", "content": user_message})

        model = "cheap"
        tool_schemas = (self.tools.list_tools() if self.tools else []) + [
            DEEP_REASONING_TOOL_SCHEMA
        ]

        reply_text = ""
        for _ in range(MAX_TOOL_ITERATIONS):
            assistant_message = await self.gateway.chat_completion(
                messages, model=model, tools=tool_schemas
            )
            tool_calls = assistant_message.get("tool_calls")

            if not tool_calls:
                reply_text = assistant_message.get("content") or ""
                break

            messages.append(assistant_message)
            for call in tool_calls:
                name = call["function"]["name"]
                raw_args = call["function"].get("arguments") or "{}"
                args = json.loads(raw_args) if raw_args else {}

                if name == "deep_reasoning":
                    model = "strong"
                    result = "Switching to deeper reasoning for this response."
                else:
                    try:
                        if self.tools is None:
                            raise ValueError(f"No tools available to handle: {name}")
                        result = await self.tools.execute(name, args)
                    except ValueError as exc:
                        result = f"Error: {exc}"

                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        else:
            reply_text = assistant_message.get("content") or (
                "I couldn't finish resolving that request."
            )

        await self.store.append_message(conversation_id, "user", user_message, None)
        await self.store.append_message(conversation_id, "assistant", reply_text, model)

        return AgentReply(text=reply_text, model_used=model)
