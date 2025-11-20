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

    async def generate_text(self, prompt: str, model: str = "gpt-4o") -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 500
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()  # Raise an exception for HTTP errors
                return response.json()
        except httpx.RequestError as exc:
            logger.error(f"An error occurred while requesting {exc.request.url!r}: {exc}", exc_info=True)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}", exc_info=True)
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")
            raise

if __name__ == "__main__":
    # Example usage (for testing purposes)
    async def main():
        client = LLMClient()
        try:
            response = await client.generate_text("What is the capital of France?")
            print(response)
        except Exception as e:
            print(f"Failed to generate text: {e}")

    import asyncio
    asyncio.run(main())
