import asyncio
from backend.app.security.rate_limiter import rate_limiter
from backend.app.core.logger import services_logger

async def run(report_id: str, token_id: str):
    """
    Mocks fetching price data for a given token.
    """
    services_logger.info(f"Price Agent: Starting to fetch price for token_id: {token_id}, report_id: {report_id}")
    services_logger.debug(f"Price Agent: Checking rate limit for token_id: {token_id}")
    if not rate_limiter.check_rate_limit("price_agent"):
        services_logger.warning(f"Price Agent: Rate limit exceeded for token_id: {token_id}, report_id: {report_id}")
        return {"error": "Rate limit exceeded for price_agent.", "token_id": token_id, "report_id": report_id}
    
    services_logger.debug(f"Price Agent: Simulating API call for token_id: {token_id}")
    await asyncio.sleep(0.1)  # Simulate a small delay
    
    response = {"price": 123.45, "token_id": token_id, "report_id": report_id}
    services_logger.info(f"Price Agent: Successfully fetched price for token_id: {token_id}, report_id: {report_id}. Response size: {len(str(response))} bytes")
    services_logger.info(f"Price Agent: Completed fetching price for token_id: {token_id}, report_id: {report_id}")
    return response
