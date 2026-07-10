import base64
import json
from collections.abc import AsyncIterator

import httpx

from app.config import settings


class LLMGatewayClient:
    """Thin wrapper over the self-hosted LiteLLM proxy's OpenAI-compatible API.

    BE code should only ever go through this client, never call a provider
    SDK directly — swapping providers/models is a LiteLLM config change,
    not a code change.

    Holds one persistent httpx.AsyncClient rather than opening a new
    connection per call — every request here targets the same LiteLLM host,
    so a fresh TLS handshake per call is pure waste (matches the pattern
    already used by SupabaseConversationStore/RAGRetriever/KnowledgeLookup).
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or settings.litellm_base_url
        self.api_key = api_key or settings.litellm_api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=60,
        )

    async def chat_completion(
        self, messages: list[dict], model: str = "cheap", tools: list[dict] | None = None
    ) -> dict:
        """Returns the raw assistant message dict (content + optional tool_calls)
        so callers can drive a tool-calling loop.
        """
        payload: dict = {"model": model, "messages": messages}
        if tools:
            payload["tools"] = tools

        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]

    async def chat_completion_stream(
        self, messages: list[dict], model: str = "cheap", tools: list[dict] | None = None
    ) -> AsyncIterator[dict]:
        """Yields {"delta": {...}, "finish_reason": ...} per SSE chunk, in
        arrival order — mirrors the OpenAI-compatible streaming chunk shape
        (confirmed live against this gateway) so callers can accumulate
        content/tool_calls deltas themselves.
        """
        payload: dict = {"model": model, "messages": messages, "stream": True}
        if tools:
            payload["tools"] = tools

        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[len("data: ") :]
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                choice = chunk["choices"][0]
                yield {"delta": choice.get("delta", {}), "finish_reason": choice.get("finish_reason")}

    async def embed(self, text: str, model: str = "embeddings") -> list[float]:
        response = await self._client.post(
            "/embeddings", json={"model": model, "input": text}
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]

    async def transcribe(
        self, audio_bytes: bytes, audio_format: str = "wav", model: str = "cheap"
    ) -> str:
        """Gemini has no working /audio/transcriptions route via LiteLLM
        (confirmed live: raises "Unmapped provider passed in") — this goes
        through the normal chat endpoint with multimodal audio input
        instead, which does work. Gemini only accepts wav/mp3/aiff/aac/
        ogg/flac input audio — the caller is responsible for handing this
        bytes in one of those formats (NOT the browser's raw webm output).
        """
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        message = await self.chat_completion(
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Transcribe this audio verbatim. Respond with only the "
                                "transcription, no commentary."
                            ),
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {"data": audio_b64, "format": audio_format},
                        },
                    ],
                }
            ],
            model=model,
        )
        return message.get("content") or ""

    async def speak(self, text: str, model: str = "tts", voice: str = "Kore") -> bytes:
        """LiteLLM's Gemini TTS route already returns a properly headered
        WAV file (confirmed live), not raw PCM — no wrapping needed here.
        """
        response = await self._client.post(
            "/audio/speech", json={"model": model, "input": text, "voice": voice}
        )
        response.raise_for_status()
        return response.content
