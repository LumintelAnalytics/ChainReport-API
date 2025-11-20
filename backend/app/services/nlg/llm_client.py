import os
import httpx
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = 30.0  # seconds
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.timeout, headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def generate_text(self, prompt: str, model: str = "gpt-4o") -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("LLMClient must be used as an async context manager or client must be explicitly opened.")

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }
        try:
            response = await self._client.post(
                self.base_url,
                json=payload
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}", exc_info=True)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}. Response text truncated: {exc.response.text[:200]}", exc_info=True)
            raise
        except Exception:
            logger.exception("An unexpected error occurred")
            raise

if __name__ == "__main__":
    # Example usage (for testing purposes)
    async def main():
        async with LLMClient() as client:
            try:
                response = await client.generate_text("What is the capital of France?")
                print(response)
            except Exception as e:
                print(f"Failed to generate text: {e}")

    import asyncio
    asyncio.run(main())
