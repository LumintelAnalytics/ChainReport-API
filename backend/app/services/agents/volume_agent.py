import asyncio
from backend.app.security.rate_limiter import rate_limiter
from backend.app.core.logger import services_logger

async def run(report_id: str, token_id: str):
    """
    Mocks fetching volume data for a given token.
    """
    services_logger.info(f"Volume Agent: Starting to fetch volume for token_id: {token_id}, report_id: {report_id}")
    services_logger.debug(f"Volume Agent: Checking rate limit for token_id: {token_id}")
    if not rate_limiter.check_rate_limit("volume_agent"):
        services_logger.warning(f"Volume Agent: Rate limit exceeded for token_id: {token_id}, report_id: {report_id}")
        return {"error": "Rate limit exceeded for volume_agent.", "token_id": token_id, "report_id": report_id}
    
    services_logger.debug(f"Volume Agent: Simulating API call for token_id: {token_id}")
    await asyncio.sleep(0.1)  # Simulate a small delay
    
    response = {"volume": 987654.32, "token_id": token_id, "report_id": report_id}
    services_logger.info(f"Volume Agent: Successfully fetched volume for token_id: {token_id}, report_id: {report_id}. Response size: {len(str(response))} bytes")
    services_logger.info(f"Volume Agent: Completed fetching volume for token_id: {token_id}, report_id: {report_id}")
    return response
