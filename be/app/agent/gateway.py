import httpx

from app.config import settings


class LLMGatewayClient:
    """Thin wrapper over the self-hosted LiteLLM proxy's OpenAI-compatible API.

    BE code should only ever go through this client, never call a provider
    SDK directly — swapping providers/models is a LiteLLM config change,
    not a code change.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url or settings.litellm_base_url
        self.api_key = api_key or settings.litellm_api_key

    async def chat_completion(
        self, messages: list[dict], model: str = "cheap", tools: list[dict] | None = None
    ) -> dict:
        """Returns the raw assistant message dict (content + optional tool_calls)
        so callers can drive a tool-calling loop.
        """
        payload: dict = {"model": model, "messages": messages}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]

    async def embed(self, text: str, model: str = "embeddings") -> list[float]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post(
                "/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "input": text},
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]

    async def transcribe(
        self, audio_bytes: bytes, filename: str = "audio.webm", model: str = "whisper"
    ) -> str:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post(
                "/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data={"model": model},
                files={"file": (filename, audio_bytes, "application/octet-stream")},
            )
            response.raise_for_status()
            return response.json()["text"]

    async def speak(self, text: str, model: str = "tts", voice: str = "alloy") -> bytes:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post(
                "/audio/speech",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "input": text, "voice": voice},
            )
            response.raise_for_status()
            return response.content
