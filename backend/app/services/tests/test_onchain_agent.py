import pytest
import httpx
from respx import MockRouter
from backend.app.services.agents.onchain_agent import (
    fetch_onchain_metrics,
    fetch_tokenomics,
    OnchainAgentTimeout,
    OnchainAgentNetworkError,
    OnchainAgentHTTPError,
    OnchainAgentException,
)

@pytest.mark.asyncio
async def test_fetch_onchain_metrics_success(respx_mock: MockRouter):
    url = "https://api.example.com/onchain_metrics"
    expected_data = {"metric1": 100, "metric2": "value"}
    respx_mock.get(url).return_value = httpx.Response(200, json=expected_data)

    result = await fetch_onchain_metrics(url)
    assert result == expected_data

@pytest.mark.asyncio
async def test_fetch_onchain_metrics_with_params_success(respx_mock: MockRouter):
    url = "https://api.example.com/onchain_metrics"
    params = {"token_id": "ETH", "period": "24h"}
    expected_data = {"metric1": 200, "token": "ETH"}
    respx_mock.get(url, params=params).return_value = httpx.Response(200, json=expected_data)

    result = await fetch_onchain_metrics(url, params=params)
    assert result == expected_data

@pytest.mark.asyncio
async def test_fetch_onchain_metrics_timeout(respx_mock: MockRouter):
    url = "https://api.example.com/onchain_metrics"
    respx_mock.get(url).mock(side_effect=httpx.TimeoutException("Request timed out", request=httpx.Request("GET", url)))

    with pytest.raises(OnchainAgentTimeout):
        await fetch_onchain_metrics(url)

@pytest.mark.asyncio
async def test_fetch_onchain_metrics_network_error(respx_mock: MockRouter):
    url = "https://api.example.com/onchain_metrics"
    respx_mock.get(url).mock(side_effect=httpx.RequestError("Network unreachable", request=httpx.Request("GET", url)))

    with pytest.raises(OnchainAgentNetworkError):
        await fetch_onchain_metrics(url)

@pytest.mark.asyncio
async def test_fetch_onchain_metrics_http_error(respx_mock: MockRouter):
    url = "https://api.example.com/onchain_metrics"
    respx_mock.get(url).return_value = httpx.Response(404, text="Not Found")

    with pytest.raises(OnchainAgentHTTPError) as excinfo:
        await fetch_onchain_metrics(url)
    assert excinfo.value.status_code == 404

@pytest.mark.asyncio
async def test_fetch_onchain_metrics_unexpected_error(respx_mock: MockRouter):
    url = "https://api.example.com/onchain_metrics"
    respx_mock.get(url).mock(side_effect=ValueError("Unexpected error"))

    with pytest.raises(OnchainAgentException):
        await fetch_onchain_metrics(url)

@pytest.mark.asyncio
async def test_fetch_tokenomics_success(respx_mock: MockRouter):
    url = "https://api.example.com/tokenomics"
    expected_data = {"supply": 1000000, "distribution": "fair"}
    respx_mock.get(url).return_value = httpx.Response(200, json=expected_data)

    result = await fetch_tokenomics(url)
    assert result == expected_data

@pytest.mark.asyncio
async def test_fetch_tokenomics_timeout(respx_mock: MockRouter):
    url = "https://api.example.com/tokenomics"
    respx_mock.get(url).mock(side_effect=httpx.TimeoutException("Request timed out", request=httpx.Request("GET", url)))

    with pytest.raises(OnchainAgentTimeout):
        await fetch_tokenomics(url)

@pytest.mark.asyncio
async def test_fetch_tokenomics_network_error(respx_mock: MockRouter):
    url = "https://api.example.com/tokenomics"
    respx_mock.get(url).mock(side_effect=httpx.RequestError("Network unreachable", request=httpx.Request("GET", url)))

    with pytest.raises(OnchainAgentNetworkError):
        await fetch_tokenomics(url)

@pytest.mark.asyncio
async def test_fetch_tokenomics_http_error(respx_mock: MockRouter):
    url = "https://api.example.com/tokenomics"
    respx_mock.get(url).return_value = httpx.Response(500, text="Internal Server Error")

    with pytest.raises(OnchainAgentHTTPError) as excinfo:
        await fetch_tokenomics(url)
    assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_fetch_tokenomics_unexpected_error(respx_mock: MockRouter):
    url = "https://api.example.com/tokenomics"
    respx_mock.get(url).mock(side_effect=KeyError("Missing key"))

    with pytest.raises(OnchainAgentException):
        await fetch_tokenomics(url)
