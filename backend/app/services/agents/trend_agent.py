import asyncio
from backend.app.security.rate_limiter import rate_limiter

async def run(report_id: str, token_id: str):
    """
    Mocks fetching trend data for a given token.
    """
    if not rate_limiter.check_rate_limit("trend_agent"):
        return {"error": "Rate limit exceeded for trend_agent.", "token_id": token_id, "report_id": report_id}
    await asyncio.sleep(0.1)  # Simulate a small delay
    return {"trend": "up", "change_24h": 5.67, "token_id": token_id, "report_id": report_id}
