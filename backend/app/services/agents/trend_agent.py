import asyncio
from backend.app.security.rate_limiter import rate_limiter
from backend.app.core.logger import services_logger

async def run(report_id: str, token_id: str):
    """
    Mocks fetching trend data for a given token.
    """
    services_logger.info(f"Trend Agent: Starting to fetch trend for token_id: {token_id}, report_id: {report_id}")
    services_logger.debug(f"Trend Agent: Checking rate limit for token_id: {token_id}")
    if not rate_limiter.check_rate_limit("trend_agent"):
        services_logger.warning(f"Trend Agent: Rate limit exceeded for token_id: {token_id}, report_id: {report_id}")
        return {"error": "Rate limit exceeded for trend_agent.", "token_id": token_id, "report_id": report_id}
    
    services_logger.debug(f"Trend Agent: Simulating API call for token_id: {token_id}")
    await asyncio.sleep(0.1)  # Simulate a small delay
    
    response = {"trend": "up", "change_24h": 5.67, "token_id": token_id, "report_id": report_id}
    services_logger.info(f"Trend Agent: Successfully fetched trend for token_id: {token_id}, report_id: {report_id}. Response size: {len(str(response))} bytes")
    services_logger.info(f"Trend Agent: Completed fetching trend for token_id: {token_id}, report_id: {report_id}")
    return response
