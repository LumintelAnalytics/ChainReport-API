import asyncio

async def run(token_id: str):
    """
    Mocks fetching trend data for a given token.
    """
    await asyncio.sleep(0.1)  # Simulate a small delay
    return {"trend": "up", "change_24h": 5.67, "token_id": token_id}
