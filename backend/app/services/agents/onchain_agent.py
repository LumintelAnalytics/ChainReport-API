import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.app.core.config import settings
from backend.app.core.logger import services_logger as logger
from backend.app.security.rate_limiter import rate_limiter

def log_retry_attempt(retry_state):
    token_id = "unknown"
    try:
        if "token_id" in retry_state.kwargs:
            token_id = retry_state.kwargs["token_id"]
        elif len(retry_state.args) > 1:
            token_id = retry_state.args[1]
    except (IndexError, KeyError):
        pass # token_id remains "unknown"

    logger.warning(
        f"OnchainAgent: Retrying {retry_state.fn.__name__} for token_id: {token_id}, "
        f"attempt {retry_state.attempt_number}, "
        f"exception: {retry_state.outcome.exception()}, "
        f"next backoff: {retry_state.next_action.sleep} seconds."
    )

# Configure httpx timeouts and limits
HTTP_TIMEOUT = httpx.Timeout(5.0, read=10.0, write=5.0, pool=5.0)
HTTP_LIMITS = httpx.Limits(max_connections=10, max_keepalive_connections=5)

class OnchainAgentException(Exception):
    """Base exception for OnchainAgent errors."""
    pass

class OnchainAgentTimeout(OnchainAgentException):
    """Exception raised for OnchainAgent timeouts."""
    pass

class OnchainAgentNetworkError(OnchainAgentException):
    """Exception raised for OnchainAgent network errors."""
    pass

class OnchainAgentHTTPError(OnchainAgentException):
    """Exception raised for non-2xx HTTP responses from OnchainAgent."""
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code

class OnchainAgentRateLimitExceeded(OnchainAgentException):
    """Exception raised when rate limit is exceeded for OnchainAgent."""
    def __init__(self, message="Rate limit exceeded for onchain_agent."):
        super().__init__(message)

@retry(
    stop=stop_after_attempt(settings.MAX_RETRIES),
    wait=wait_exponential(multiplier=settings.RETRY_MULTIPLIER, min=settings.MIN_RETRY_DELAY, max=settings.MAX_RETRY_DELAY),
    retry=retry_if_exception_type((OnchainAgentTimeout, OnchainAgentNetworkError, OnchainAgentHTTPError, httpx.TimeoutException, httpx.RequestError)),
    reraise=True,
    before_sleep=log_retry_attempt
)
async def fetch_onchain_metrics(url: str, token_id: str, params: dict | None = None) -> dict:
    """
    Fetches on-chain metrics from a specified URL.

    Args:
        url: The URL to fetch metrics from.
        token_id: Token ID for request tracing and log correlation.
        params: Optional dictionary of query parameters.

    Returns:
        A dictionary containing the fetched on-chain metrics.

    Raises:
        OnchainAgentTimeout: If the request times out.
        OnchainAgentNetworkError: If a network-related error occurs.
        OnchainAgentHTTPError: If the HTTP response status is not 2xx.
        OnchainAgentException: For other unexpected errors.
    """
    logger.info(f"OnchainAgent: Starting fetch_onchain_metrics for token_id: {token_id}, URL: {url}")
    if params is None:
        params = {}

    logger.info(f"[Token ID: {token_id}] Initiating API call to {url} with params: {params}")

    if not rate_limiter.check_rate_limit("onchain_agent"):
        logger.warning(f"[Token ID: {token_id}] Rate limit exceeded for onchain_agent.")
        raise OnchainAgentRateLimitExceeded()

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS, headers={"User-Agent": settings.USER_AGENT}) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            response_json = response.json()
            output_size = len(response.content)
            logger.info(f"[Token ID: {token_id}] API call to {url} successful. Status: {response.status_code}, Response size: {output_size} bytes")
            await asyncio.sleep(settings.REQUEST_DELAY_SECONDS)
            logger.info(f"OnchainAgent: Completed fetch_onchain_metrics for token_id: {token_id}, URL: {url}")
            return response_json
        except httpx.TimeoutException as e:
            logger.error(f"[Token ID: {token_id}] Timeout fetching on-chain metrics from {url}: {e}")
            raise OnchainAgentTimeout(f"Request to {url} timed out.") from e
        except httpx.RequestError as e:
            logger.error(f"[Token ID: {token_id}] Network error fetching on-chain metrics from {url}: {e}")
            raise OnchainAgentNetworkError(f"Network error for {url}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"[Token ID: {token_id}] HTTP error fetching on-chain metrics from {url}: {e.response.status_code}. Response text truncated: {e.response.text[:200]}")
            raise OnchainAgentHTTPError(f"HTTP error for {url}: {e.response.status_code}", e.response.status_code) from e
        except Exception as e:
            raise OnchainAgentException(f"Unexpected error for {url}") from e

@retry(
    stop=stop_after_attempt(settings.MAX_RETRIES),
    wait=wait_exponential(multiplier=settings.RETRY_MULTIPLIER, min=settings.MIN_RETRY_DELAY, max=settings.MAX_RETRY_DELAY),
    retry=retry_if_exception_type((OnchainAgentTimeout, OnchainAgentNetworkError, OnchainAgentHTTPError, httpx.TimeoutException, httpx.RequestError)),
    reraise=True,
    before_sleep=log_retry_attempt
)
async def fetch_tokenomics(url: str, token_id: str, params: dict | None = None) -> dict:
    """
    Fetches tokenomics data from a specified URL.

    Args:
        url: The URL to fetch tokenomics data from.
        token_id: The token ID for traceability.
        params: Optional dictionary of query parameters.

    Returns:
        A dictionary containing the fetched tokenomics data.

    Raises:
        OnchainAgentTimeout: If the request times out.
        OnchainAgentNetworkError: If a network-related error occurs.
        OnchainAgentHTTPError: If the HTTP response status is not 2xx.
        OnchainAgentException: For other unexpected errors.
    """
    logger.info(f"OnchainAgent: Starting fetch_tokenomics for token_id: {token_id}, URL: {url}")
    if params is None:
        params = {}

    logger.info(f"[Token ID: {token_id}] Initiating API call to {url} with params: {params}")

    if not rate_limiter.check_rate_limit("onchain_agent"):
        logger.warning(f"[Token ID: {token_id}] Rate limit exceeded for onchain_agent.")
        raise OnchainAgentRateLimitExceeded()

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS, headers={"User-Agent": settings.USER_AGENT}) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            response_json = response.json()
            output_size = len(str(response_json))
            logger.info(f"[Token ID: {token_id}] API call to {url} successful. Status: {response.status_code}, Output size: {output_size} bytes")
            await asyncio.sleep(settings.REQUEST_DELAY_SECONDS)
            logger.info(f"OnchainAgent: Completed fetch_tokenomics for token_id: {token_id}, URL: {url}")
            return response_json
        except httpx.TimeoutException as e:
            logger.error(f"[Token ID: {token_id}] Timeout fetching tokenomics data from {url}: {e}")
            raise OnchainAgentTimeout(f"Request to {url} timed out.") from e
        except httpx.RequestError as e:
            logger.error(f"[Token ID: {token_id}] Network error fetching tokenomics data from {url}: {e}")
            raise OnchainAgentNetworkError(f"Network error for {url}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"[Token ID: {token_id}] HTTP error fetching tokenomics data from {url}: {e.response.status_code}. Response text truncated: {e.response.text[:200]}")
            raise OnchainAgentHTTPError(f"HTTP error for {url}: {e.response.status_code}", e.response.status_code) from e
        except Exception as e:
            logger.exception(f"[Token ID: {token_id}] An unexpected error occurred while fetching tokenomics data from {url}")
            raise OnchainAgentException(f"Unexpected error for {url}") from e
