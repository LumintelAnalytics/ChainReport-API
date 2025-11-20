import pytest
import respx
from httpx import Response, Request
import httpx
from backend.app.services.nlg.llm_client import LLMClient
import os

# Mock the environment variable for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    yield
    del os.environ["OPENAI_API_KEY"]

@pytest.mark.asyncio
async def test_generate_text_success():    async with LLMClient() as client:
    expected_response_payload = {
        "choices": [{
            "message": {"content": "The capital of France is Paris."}
        }]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_response_payload)

        prompt = "What is the capital of France?"
        response = await client.generate_text(prompt)

        assert response == expected_response_payload
        assert respx_mock.calls.call_count == 1
        request = respx_mock.calls.last.request
        assert request.method == "POST"
        assert request.url == "https://api.openai.com/v1/chat/completions"
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test_api_key"

@pytest.mark.asyncio
async def test_generate_text_http_error():
    async with LLMClient() as client:

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(500, text="Internal Server Error")

        prompt = "Generate an error"
        with pytest.raises(Exception) as excinfo:
            await client.generate_text(prompt)
        assert "500" in str(excinfo.value) and "Internal Server Error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_text_request_error():
    async with LLMClient() as client:

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").mock(side_effect=httpx.RequestError("Connection refused", request=Request("POST", "https://api.openai.com")))

        prompt = "Generate a request error"
        with pytest.raises(Exception) as excinfo:
            await client.generate_text(prompt)
        assert "Connection refused" in str(excinfo.value)
