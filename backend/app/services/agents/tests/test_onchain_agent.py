import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from tenacity import wait_fixed, stop_after_attempt, retry
from backend.app.services.agents.onchain_agent import (
    fetch_onchain_metrics,
    fetch_tokenomics,
    OnchainAgentTimeout,
    OnchainAgentNetworkError,
    OnchainAgentHTTPError,
    OnchainAgentException
)

# Helper to create a mock httpx.Response
def create_mock_response(status_code: int, json_data: dict = None, text_data: str = None):
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data if json_data is not None else {}
    mock_response.text = text_data if text_data is not None else ""
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        f"Error response {status_code}", request=httpx.Request("GET", "http://test.com"), response=mock_response
    ) if status_code >= 400 else None
    return mock_response

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_retry_on_timeout(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 2 timeouts, then success
    mock_client_instance.get.side_effect = [
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
        create_mock_response(200, {"data": "onchain_metrics"})
    ]

    # Temporarily override retry settings for faster test execution
    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics.retry') as mock_retry_decorator:
        mock_retry_decorator.return_value = lambda func: retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01), reraise=True)(func)
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain")
        assert result == {"data": "onchain_metrics"}
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_retry_on_network_error(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 2 network errors, then success
    mock_client_instance.get.side_effect = [
        httpx.RequestError("Network error", request=httpx.Request("GET", "http://test.com")),
        httpx.RequestError("Network error", request=httpx.Request("GET", "http://test.com")),
        create_mock_response(200, {"data": "onchain_metrics"})
    ]

    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics.retry') as mock_retry_decorator:
        mock_retry_decorator.return_value = lambda func: retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01), reraise=True)(func)
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain")
        assert result == {"data": "onchain_metrics"}
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_retry_on_http_error(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 2 HTTP 500 errors, then success
    mock_client_instance.get.side_effect = [
        create_mock_response(500),
        create_mock_response(500),
        create_mock_response(200, {"data": "onchain_metrics"})
    ]

    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics.retry') as mock_retry_decorator:
        mock_retry_decorator.return_value = lambda func: retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01), reraise=True)(func)
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain")
        assert result == {"data": "onchain_metrics"}
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_max_retries_exceeded(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 3 timeouts, exceeding retry limit
    mock_client_instance.get.side_effect = [
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
    ]

    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics.retry') as mock_retry_decorator:
        mock_retry_decorator.return_value = lambda func: retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01), reraise=True)(func)
        
        with pytest.raises(OnchainAgentTimeout):
            await fetch_onchain_metrics(url="http://test.com/onchain")
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_retry_on_timeout(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 2 timeouts, then success
    mock_client_instance.get.side_effect = [
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
        httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
        create_mock_response(200, {"data": "tokenomics"})
    ]

    with patch('backend.app.services.agents.onchain_agent.fetch_tokenomics.retry') as mock_retry_decorator:
        mock_retry_decorator.return_value = lambda func: retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01), reraise=True)(func)
        
        result = await fetch_tokenomics(url="http://test.com/tokenomics")
        assert result == {"data": "tokenomics"}
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_max_retries_exceeded(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 3 network errors, exceeding retry limit
    mock_client_instance.get.side_effect = [
        httpx.RequestError("Network error", request=httpx.Request("GET", "http://test.com")),
        httpx.RequestError("Network error", request=httpx.Request("GET", "http://test.com")),
        httpx.RequestError("Network error", request=httpx.Request("GET", "http://test.com")),
    ]

    with patch('backend.app.services.agents.onchain_agent.fetch_tokenomics.retry') as mock_retry_decorator:
        mock_retry_decorator.return_value = lambda func: retry(stop=stop_after_attempt(3), wait=wait_fixed(0.01), reraise=True)(func)
        
        with pytest.raises(OnchainAgentNetworkError):
            await fetch_tokenomics(url="http://test.com/tokenomics")
        assert mock_client_instance.get.call_count == 3
