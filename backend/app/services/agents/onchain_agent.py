import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

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

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((OnchainAgentTimeout, OnchainAgentNetworkError, OnchainAgentHTTPError, httpx.TimeoutException, httpx.RequestError)),
    reraise=True
)
async def fetch_onchain_metrics(url: str, params: dict = None) -> dict:
    """
    Fetches on-chain metrics from a specified URL.

    Args:
        url: The URL to fetch metrics from.
        params: Optional dictionary of query parameters.

    Returns:
        A dictionary containing the fetched on-chain metrics.

    Raises:
        OnchainAgentTimeout: If the request times out.
        OnchainAgentNetworkError: If a network-related error occurs.
        OnchainAgentHTTPError: If the HTTP response status is not 2xx.
        OnchainAgentException: For other unexpected errors.
    """
    if params is None:
        params = {}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS) as client:
        try:
            logger.info(f"Fetching on-chain metrics from: {url} with params: {params}")
            response = await client.get(url, params=params)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching on-chain metrics from {url}: {e}")
            raise OnchainAgentTimeout(f"Request to {url} timed out.") from e
        except httpx.RequestError as e:
            logger.error(f"Network error fetching on-chain metrics from {url}: {e}")
            raise OnchainAgentNetworkError(f"Network error for {url}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching on-chain metrics from {url}: {e.response.status_code} - {e.response.text}")
            raise OnchainAgentHTTPError(f"HTTP error for {url}: {e.response.status_code}", e.response.status_code) from e
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching on-chain metrics from {url}: {e}")
            raise OnchainAgentException(f"Unexpected error for {url}: {e}") from e

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((OnchainAgentTimeout, OnchainAgentNetworkError, OnchainAgentHTTPError, httpx.TimeoutException, httpx.RequestError)),
    reraise=True
)
async def fetch_tokenomics(url: str, params: dict = None) -> dict:
    """
    Fetches tokenomics data from a specified URL.

    Args:
        url: The URL to fetch tokenomics data from.
        params: Optional dictionary of query parameters.

    Returns:
        A dictionary containing the fetched tokenomics data.

    Raises:
        OnchainAgentTimeout: If the request times out.
        OnchainAgentNetworkError: If a network-related error occurs.
        OnchainAgentHTTPError: If the HTTP response status is not 2xx.
        OnchainAgentException: For other unexpected errors.
    """
    if params is None:
        params = {}

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, limits=HTTP_LIMITS) as client:
        try:
            logger.info(f"Fetching tokenomics data from: {url} with params: {params}")
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"Timeout fetching tokenomics data from {url}: {e}")
            raise OnchainAgentTimeout(f"Request to {url} timed out.") from e
        except httpx.RequestError as e:
            logger.error(f"Network error fetching tokenomics data from {url}: {e}")
            raise OnchainAgentNetworkError(f"Network error for {url}: {e}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching tokenomics data from {url}: {e.response.status_code} - {e.response.text}")
            raise OnchainAgentHTTPError(f"HTTP error for {url}: {e.response.status_code}", e.response.status_code) from e
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching tokenomics data from {url}: {e}")
            raise OnchainAgentException(f"Unexpected error for {url}: {e}") from e
