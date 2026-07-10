import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from app.agent.gateway import LLMGatewayClient
from app.agent.store import ConversationStore, NullConversationStore

# Always present, regardless of whether retrieval succeeds — identity/persona
# must not depend on RAG working. Grounding context (below) is layered on
# top of this, not a replacement for it.
PERSONA_INSTRUCTIONS = (
    "You are syamsulhudauul's AI representative, speaking to recruiters and "
    "clients who want to know about his skills, experience, and projects. "
    "Stay in this persona at all times — including for meta or off-topic "
    "questions like who or what you are, or what model/company powers you. "
    "Never reveal that you are an LLM, and never name an AI provider or "
    "vendor (e.g. Google, OpenAI, Anthropic). For such questions, briefly "
    "decline and redirect to what you can actually help with: his skills, "
    "experience, projects, and contact info."
)

GROUNDING_INSTRUCTIONS = (
    "Answer questions about syamsulhudauul using only the following "
    "grounding context. If the answer isn't covered by the context, say "
    "you don't have that information rather than guessing."
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


def _merge_tool_call_delta(accumulated: dict[int, dict], delta_tool_calls: list[dict]) -> None:
    """Streamed tool calls arrive fragmented across chunks, keyed by index —
    id/name usually only on the first fragment, arguments concatenated
    across all of them (confirmed live against this gateway).
    """
    for tc in delta_tool_calls:
        index = tc.get("index", 0)
        entry = accumulated.setdefault(index, {"id": None, "name": None, "arguments": ""})
        if tc.get("id"):
            entry["id"] = tc["id"]
        func = tc.get("function") or {}
        if func.get("name"):
            entry["name"] = func["name"]
        if func.get("arguments"):
            entry["arguments"] += func["arguments"]


class AgentCore:
    """Transport-agnostic reasoning core.

    run_turn() returns the complete reply — used by voice, which needs the
    full text before it can synthesize speech. run_turn_stream() yields the
    final answer incrementally for chat's SSE endpoint. Both share the same
    grounding/persona/tool-loop/persistence logic.
    """

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

    async def _retrieve_safe(self, user_message: str) -> list[dict]:
        if self.retriever is None:
            return []
        try:
            return await self.retriever.retrieve(user_message)
        except Exception:
            # A flaky/misconfigured embeddings provider shouldn't 500 the
            # whole turn — degrade to an ungrounded reply instead.
            return []

    async def _build_initial_messages(
        self, conversation_id: str, user_message: str
    ) -> list[dict]:
        # History and retrieval are independent reads — fetch concurrently
        # instead of paying for both round trips serially.
        history, chunks = await asyncio.gather(
            self.store.get_history(conversation_id),
            self._retrieve_safe(user_message),
        )

        system_content = PERSONA_INSTRUCTIONS
        if chunks:
            context = "\n\n".join(
                f"[{chunk['source_doc']}] {chunk['content']}" for chunk in chunks
            )
            system_content = f"{PERSONA_INSTRUCTIONS}\n\n{GROUNDING_INSTRUCTIONS}\n\n{context}"

        messages = [{"role": "system", "content": system_content}, *history]
        messages.append({"role": "user", "content": user_message})
        return messages

    def _tool_schemas(self) -> list[dict]:
        return (self.tools.list_tools() if self.tools else []) + [DEEP_REASONING_TOOL_SCHEMA]

    async def _execute_tool_call(self, name: str, args: dict) -> tuple[str, str | None]:
        """Returns (result_text, escalated_model_or_None)."""
        if name == "deep_reasoning":
            return "Switching to deeper reasoning for this response.", "strong"
        try:
            if self.tools is None:
                raise ValueError(f"No tools available to handle: {name}")
            result = await self.tools.execute(name, args)
        except ValueError as exc:
            result = f"Error: {exc}"
        return result, None

    async def run_turn(self, conversation_id: str, user_message: str) -> AgentReply:
        messages = await self._build_initial_messages(conversation_id, user_message)
        model = "cheap"
        tool_schemas = self._tool_schemas()

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

                result, escalated_model = await self._execute_tool_call(name, args)
                if escalated_model:
                    model = escalated_model

                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        else:
            reply_text = assistant_message.get("content") or (
                "I couldn't finish resolving that request."
            )

        # Independent writes — no need to serialize them.
        await asyncio.gather(
            self.store.append_message(conversation_id, "user", user_message, None),
            self.store.append_message(conversation_id, "assistant", reply_text, model),
        )

        return AgentReply(text=reply_text, model_used=model)

    async def run_turn_stream(
        self, conversation_id: str, user_message: str
    ) -> AsyncIterator[dict]:
        """Yields {"type": "token", "text": ...} as the final answer streams
        in, then a single {"type": "done", "model_used": ..., "text": ...}.

        Tool-resolution iterations are never streamed to the caller — only
        the iteration that ends up producing the final content (no more
        tool_calls) streams live. This is safe because a single streamed
        response here never mixes content and tool_calls in the same turn
        (confirmed live against this gateway).
        """
        messages = await self._build_initial_messages(conversation_id, user_message)
        model = "cheap"
        tool_schemas = self._tool_schemas()

        reply_text = ""
        for _ in range(MAX_TOOL_ITERATIONS):
            content_parts: list[str] = []
            tool_calls_acc: dict[int, dict] = {}
            role = "assistant"

            async for event in self.gateway.chat_completion_stream(
                messages, model=model, tools=tool_schemas
            ):
                delta = event["delta"]
                if delta.get("role"):
                    role = delta["role"]
                if delta.get("tool_calls"):
                    _merge_tool_call_delta(tool_calls_acc, delta["tool_calls"])
                if delta.get("content"):
                    content_parts.append(delta["content"])
                    if not tool_calls_acc:
                        yield {"type": "token", "text": delta["content"]}

            if not tool_calls_acc:
                reply_text = "".join(content_parts)
                break

            tool_calls_list = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in tool_calls_acc.values()
            ]
            messages.append({"role": role, "content": None, "tool_calls": tool_calls_list})

            for call in tool_calls_list:
                name = call["function"]["name"]
                raw_args = call["function"].get("arguments") or "{}"
                args = json.loads(raw_args) if raw_args else {}

                result, escalated_model = await self._execute_tool_call(name, args)
                if escalated_model:
                    model = escalated_model

                messages.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": result}
                )
        else:
            reply_text = "".join(content_parts) or "I couldn't finish resolving that request."
            if reply_text:
                yield {"type": "token", "text": reply_text}

        await asyncio.gather(
            self.store.append_message(conversation_id, "user", user_message, None),
            self.store.append_message(conversation_id, "assistant", reply_text, model),
        )

        yield {"type": "done", "model_used": model, "text": reply_text}
