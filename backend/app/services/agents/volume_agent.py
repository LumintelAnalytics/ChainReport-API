import asyncio

async def run(token_id: str):
    """
    Mocks fetching volume data for a given token.
    """
    await asyncio.sleep(0.1)  # Simulate a small delay
    return {"volume": 987654.32, "token_id": token_id}
