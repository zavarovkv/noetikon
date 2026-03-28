import httpx
from anthropic import AsyncAnthropic


class LLMService:
    def __init__(self, api_key: str, proxy_url: str):
        http_client = httpx.AsyncClient(proxy=proxy_url)
        self.client = AsyncAnthropic(api_key=api_key, http_client=http_client)

    async def chat(
        self,
        messages: list[dict],
        system: str = "",
        max_tokens: int = 4096,
        model: str = "claude-sonnet-4-20250514",
    ) -> tuple[str, int, int]:
        """Returns (response_text, input_tokens, output_tokens)."""
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        text = response.content[0].text
        return text, response.usage.input_tokens, response.usage.output_tokens

    async def close(self):
        await self.client._client.aclose()
