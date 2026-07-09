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

    async def chat(self, messages: list[dict], model: str = "cheap") -> str:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60) as client:
            response = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": messages},
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
