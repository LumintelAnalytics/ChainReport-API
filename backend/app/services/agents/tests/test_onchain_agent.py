import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from tenacity import wait_fixed, stop_after_attempt
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
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"Error response {status_code}", request=httpx.Request("GET", "http://test.com"), response=mock_response
        )
    else:
        mock_response.raise_for_status.return_value = None
    return mock_response

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_retry_on_timeout(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        
        # Simulate 2 timeouts, then success
        mock_client_instance.get.side_effect = [
            httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
            httpx.TimeoutException("Read timeout", request=httpx.Request("GET", "http://test.com")),
            create_mock_response(200, {"data": "onchain_metrics"})
        ]
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
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

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
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

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
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

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        
        with pytest.raises(OnchainAgentTimeout):
            await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_retry_on_rate_limit(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 2 HTTP 429 errors, then success
    mock_client_instance.get.side_effect = [
        create_mock_response(429, text_data="Too Many Requests"),
        create_mock_response(429, text_data="Too Many Requests"),
        create_mock_response(200, {"data": "onchain_metrics"})
    ]

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        
        result = await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
        assert result == {"data": "onchain_metrics"}
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_retry_on_rate_limit(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate 2 HTTP 429 errors, then success
    mock_client_instance.get.side_effect = [
        create_mock_response(429, text_data="Too Many Requests"),
        create_mock_response(429, text_data="Too Many Requests"),
        create_mock_response(200, {"data": "tokenomics"})
    ]

    with patch.object(fetch_tokenomics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_tokenomics.retry, 'stop', new=stop_after_attempt(3)):
        
        result = await fetch_tokenomics(url="http://test.com/tokenomics")
        assert result == {"data": "tokenomics"}
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

    with patch.object(fetch_tokenomics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_tokenomics.retry, 'stop', new=stop_after_attempt(3)):
        
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

    with patch.object(fetch_tokenomics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_tokenomics.retry, 'stop', new=stop_after_attempt(3)):
        
        with pytest.raises(OnchainAgentNetworkError):
            await fetch_tokenomics(url="http://test.com/tokenomics")
        assert mock_client_instance.get.call_count == 3

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_http_error_raises_onchainagenthttperror(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    mock_client_instance.get.side_effect = [
        create_mock_response(404),
        create_mock_response(404),
        create_mock_response(404) # All attempts fail
    ]

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        with pytest.raises(OnchainAgentHTTPError) as excinfo:
            await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
        assert excinfo.value.status_code == 404
        assert mock_client_instance.get.call_count == 3 # Retries should still happen

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_unexpected_error_raises_onchainagentexception(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    mock_client_instance.get.side_effect = [
        Exception("Unexpected error"),
        Exception("Unexpected error"),
        Exception("Unexpected error")
    ]

    with patch.object(fetch_onchain_metrics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_onchain_metrics.retry, 'stop', new=stop_after_attempt(3)):
        with pytest.raises(OnchainAgentException):
            await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
        assert mock_client_instance.get.call_count == 3 # Retries should still happen

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_http_error_raises_onchainagenthttperror(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    mock_client_instance.get.side_effect = [
        create_mock_response(403),
        create_mock_response(403),
        create_mock_response(403)
    ]

    with patch.object(fetch_tokenomics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_tokenomics.retry, 'stop', new=stop_after_attempt(3)):
        with pytest.raises(OnchainAgentHTTPError) as excinfo:
            await fetch_tokenomics(url="http://test.com/tokenomics")
        assert excinfo.value.status_code == 403
        assert mock_client_instance.get.call_count == 3 # Retries should still happen

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_unexpected_error_raises_onchainagentexception(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance
    mock_client_instance.get.side_effect = [
        Exception("Another unexpected error"),
        Exception("Another unexpected error"),
        Exception("Another unexpected error")
    ]

    with patch.object(fetch_tokenomics.retry, 'wait', new=wait_fixed(0.01)), \
         patch.object(fetch_tokenomics.retry, 'stop', new=stop_after_attempt(3)):
        with pytest.raises(OnchainAgentException):
            await fetch_tokenomics(url="http://test.com/tokenomics")
        assert mock_client_instance.get.call_count == 3 # Retries should still happen

# --- New tests for successful fetching and schema validation ---

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_success_and_schema(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    expected_metrics = {
        "total_transactions": 1000,
        "active_users": 500,
        "average_transaction_value": 150.75,
        "timestamp": "2023-10-27T10:00:00Z"
    }
    mock_client_instance.get.return_value = create_mock_response(200, expected_metrics)

    result = await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
    assert result == expected_metrics
    assert "total_transactions" in result
    assert "active_users" in result
    assert "average_transaction_value" in result
    assert "timestamp" in result
    assert isinstance(result["total_transactions"], int)
    assert isinstance(result["active_users"], int)
    assert isinstance(result["average_transaction_value"], float)
    assert isinstance(result["timestamp"], str)

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_success_and_schema(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    expected_tokenomics = {
        "total_supply": "1000000000",
        "circulating_supply": "800000000",
        "market_cap_usd": "1500000000.50",
        "token_price_usd": "1.50",
        "last_updated": "2023-10-27T10:00:00Z"
    }
    mock_client_instance.get.return_value = create_mock_response(200, expected_tokenomics)

    result = await fetch_tokenomics(url="http://test.com/tokenomics")
    assert result == expected_tokenomics
    assert "total_supply" in result
    assert "circulating_supply" in result
    assert "market_cap_usd" in result
    assert "token_price_usd" in result
    assert "last_updated" in result
    assert isinstance(result["total_supply"], str)
    assert isinstance(result["circulating_supply"], str)
    assert isinstance(result["market_cap_usd"], str)
    assert isinstance(result["token_price_usd"], str)
    assert isinstance(result["last_updated"], str)

# --- New tests for handling missing fields ---

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_missing_fields(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate a response with some missing fields
    incomplete_metrics = {
        "total_transactions": 1234,
        "timestamp": "2023-10-27T11:00:00Z"
    }
    mock_client_instance.get.return_value = create_mock_response(200, incomplete_metrics)

    result = await fetch_onchain_metrics(url="http://test.com/onchain", token_id="test_token_id")
    assert result == incomplete_metrics
    # The agent should return whatever it gets, schema validation is typically done downstream
    assert "total_transactions" in result
    assert "active_users" not in result
    assert "average_transaction_value" not in result
    assert "timestamp" in result

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_missing_fields(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate a response with some missing fields
    incomplete_tokenomics = {
        "total_supply": "999999999",
        "token_price_usd": "2.10"
    }
    mock_client_instance.get.return_value = create_mock_response(200, incomplete_tokenomics)

    result = await fetch_tokenomics(url="http://test.com/tokenomics")
    assert result == incomplete_tokenomics
    assert "total_supply" in result
    assert "circulating_supply" not in result
    assert "market_cap_usd" not in result
    assert "token_price_usd" in result
    assert "last_updated" not in result

# --- New tests for invalid token IDs (simulated via API response) ---

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_onchain_metrics_invalid_token_id(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate an API response indicating an invalid token ID (e.g., 400 Bad Request)
    error_response_data = {"error": "Invalid token ID provided"}
    mock_client_instance.get.return_value = create_mock_response(400, error_response_data)

    with pytest.raises(OnchainAgentHTTPError) as excinfo:
        await fetch_onchain_metrics(url="http://test.com/onchain", token_id="invalid")
    assert excinfo.value.status_code == 400

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_fetch_tokenomics_invalid_token_id(mock_async_client):
    mock_client_instance = AsyncMock()
    mock_async_client.return_value.__aenter__.return_value = mock_client_instance

    # Simulate an API response indicating an invalid token ID (e.g., 404 Not Found)
    error_response_data = {"message": "Token not found"}
    mock_client_instance.get.return_value = create_mock_response(404, error_response_data)

    with pytest.raises(OnchainAgentHTTPError) as excinfo:
        await fetch_tokenomics(url="http://test.com/tokenomics", params={"token_id": "nonexistent"})
    assert excinfo.value.status_code == 404