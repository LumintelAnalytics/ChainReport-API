import asyncio

async def run(token_id: str):
    """
    Mocks fetching price data for a given token.
    """
    await asyncio.sleep(0.1)  # Simulate a small delay
    return {"price": 123.45, "token_id": token_id}
