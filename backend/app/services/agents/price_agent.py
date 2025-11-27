import asyncio
from backend.app.security.rate_limiter import rate_limiter

async def run(report_id: str, token_id: str):
    """
    Mocks fetching price data for a given token.
    """
    if not rate_limiter.check_rate_limit("price_agent"):
        return {"error": "Rate limit exceeded for price_agent.", "token_id": token_id, "report_id": report_id}
    await asyncio.sleep(0.1)  # Simulate a small delay
    return {"price": 123.45, "token_id": token_id, "report_id": report_id}
