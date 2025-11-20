import pytest
import respx
from httpx import Response
import os
import json
from typing import Dict, Any

from backend.app.services.nlg.nlg_engine import NLGEngine
from backend.app.services.nlg.llm_client import LLMClient

# Concrete implementation of NLGEngine for testing
class ConcreteNLGEngine(NLGEngine):
    async def generate_section_text(self, section_id: str, raw_data: dict) -> str:
        return self._format_output({"section_id": section_id, "text": "Mocked base section text."})

    async def generate_full_report(self, data: dict) -> str:
        sections = []
        sections.append(json.loads(await super().generate_tokenomics_text(data.get("tokenomics_data", {}))))
        sections.append(json.loads(await super().generate_onchain_text(data.get("onchain_data", {}))))
        sections.append(json.loads(await super().generate_sentiment_text(data.get("sentiment_data", {}))))
        sections.append(json.loads(await super().generate_code_audit_text(data.get("code_data", {}), data.get("audit_data", {}))))
        return self._format_output({"sections": sections})

# Mock the environment variable for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    yield
    del os.environ["OPENAI_API_KEY"]

@pytest.mark.asyncio
async def test_generate_onchain_text_success():
    engine = ConcreteNLGEngine() # Use the concrete implementation
    raw_data = {
        "active_addresses": 1000,
        "holders": 500,
        "transaction_flows": "10M USD",
        "liquidity": "20M USD"
    }
    expected_llm_response = {
        "choices": [{"message": {"content": "On-chain metrics show strong activity with 1000 active addresses and 500 holders. Transaction flows are at 10M USD and liquidity is 20M USD."}}]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_llm_response)

        response = await engine.generate_onchain_text(raw_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "onchain_metrics"
        assert "On-chain metrics show strong activity" in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_onchain_text_empty_data():
    engine = ConcreteNLGEngine() # Use the concrete implementation
    raw_data = {}

    response = await engine.generate_onchain_text(raw_data)
    parsed_response = json.loads(response)

    assert parsed_response["section_id"] == "onchain_metrics"
    assert "On-chain metrics data is not available at this time." in parsed_response["text"]

@pytest.mark.asyncio
async def test_generate_onchain_text_incomplete_data():
    engine = ConcreteNLGEngine() # Use the concrete implementation
    raw_data = {
        "active_addresses": 1000,
        "holders": 500,
    }
    expected_llm_response = {
        "choices": [{"message": {"content": "On-chain metrics show strong activity with 1000 active addresses and 500 holders. Transaction flows and liquidity data are not available."}}]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_llm_response)

        response = await engine.generate_onchain_text(raw_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "onchain_metrics"
        assert "On-chain metrics show strong activity" in parsed_response["text"]
        assert "Transaction flows and liquidity data are not available." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_onchain_text_llm_error():
    engine = ConcreteNLGEngine() # Use the concrete implementation
    raw_data = {
        "active_addresses": 1000,
        "holders": 500,
        "transaction_flows": "10M USD",
        "liquidity": "20M USD"
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(500, text="Internal Server Error")

        response = await engine.generate_onchain_text(raw_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "onchain_metrics"
        assert "Failed to generate on-chain metrics summary due to an internal error." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_onchain_text_llm_empty_content():
    engine = ConcreteNLGEngine() # Use the concrete implementation
    raw_data = {
        "active_addresses": 1000,
        "holders": 500,
        "transaction_flows": "10M USD",
        "liquidity": "20M USD"
    }
    expected_llm_response = {
        "choices": [{"message": {"content": ""}}]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_llm_response)

        response = await engine.generate_onchain_text(raw_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "onchain_metrics"
        assert "Failed to generate on-chain metrics summary due to an internal error." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_sentiment_text_success():
    engine = ConcreteNLGEngine()
    raw_data = {
        "overall_sentiment_score": 0.75,
        "community_perception": "positive",
        "trends": ["growing adoption", "strong community engagement"],
        "direction": "upward"
    }
    expected_llm_response = {
        "choices": [{"message": {"content": "Overall sentiment is highly positive (0.75) with a strong upward community direction. Key trends include growing adoption and strong community engagement."}}]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_llm_response)

        response = await engine.generate_sentiment_text(raw_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "social_sentiment"
        assert "Overall sentiment is highly positive (0.75)" in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_sentiment_text_empty_data():
    engine = ConcreteNLGEngine()
    raw_data = {}

    response = await engine.generate_sentiment_text(raw_data)
    parsed_response = json.loads(response)

    assert parsed_response["section_id"] == "social_sentiment"
    assert "Social sentiment data is not available at this time." in parsed_response["text"]

@pytest.mark.asyncio
async def test_generate_sentiment_text_llm_error():
    engine = ConcreteNLGEngine()
    raw_data = {
        "overall_sentiment_score": 0.75,
        "community_perception": "positive"
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(500, text="Internal Server Error")

        response = await engine.generate_sentiment_text(raw_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "social_sentiment"
        assert "Failed to generate social sentiment summary due to an internal error." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

        assert parsed_response["section_id"] == "social_sentiment"
        assert "Failed to generate social sentiment summary due to an internal error." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_code_audit_text_success():
    engine = ConcreteNLGEngine()
    code_data = {"files": [{"name": "main.py", "lines": 100}]}
    audit_data = {"risks": [{"type": "security", "severity": "high"}]}
    expected_llm_response = {
        "choices": [{"message": {"content": "Code audit summary: Clarity is good. High security risk identified. Recent code activity. Good repository quality."}}]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_llm_response)

        response = await engine.generate_code_audit_text(code_data, audit_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "code_audit_summary"
        assert "Code audit summary: Clarity is good." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_code_audit_text_empty_data():
    engine = ConcreteNLGEngine()
    code_data = {}
    audit_data = {}

    response = await engine.generate_code_audit_text(code_data, audit_data)
    parsed_response = json.loads(response)

    assert parsed_response["section_id"] == "code_audit_summary"
    assert "Code audit and repository data are not available at this time." in parsed_response["text"]

@pytest.mark.asyncio
async def test_generate_code_audit_text_llm_error():
    engine = ConcreteNLGEngine()
    code_data = {"files": [{"name": "main.py", "lines": 100}]}
    audit_data = {"risks": [{"type": "security", "severity": "high"}]}

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(500, text="Internal Server Error")

        response = await engine.generate_code_audit_text(code_data, audit_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "code_audit_summary"
        assert "Failed to generate code audit summary due to an internal error." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_code_audit_text_llm_empty_content():
    engine = ConcreteNLGEngine()
    code_data = {"files": [{"name": "main.py", "lines": 100}]}
    audit_data = {"risks": [{"type": "security", "severity": "high"}]}
    expected_llm_response = {
        "choices": [{"message": {"content": ""}}]
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").return_value = Response(200, json=expected_llm_response)

        response = await engine.generate_code_audit_text(code_data, audit_data)
        parsed_response = json.loads(response)

        assert parsed_response["section_id"] == "code_audit_summary"
        assert "Failed to generate code audit summary due to an internal error." in parsed_response["text"]
        assert respx_mock.calls.call_count == 1

@pytest.mark.asyncio
async def test_generate_full_report_success():
    engine = ConcreteNLGEngine()
    
    mock_tokenomics_data = {"key": "value"}
    mock_onchain_data = {"active_addresses": 1000}
    mock_sentiment_data = {"score": 0.8}
    mock_code_data = {"files": ["file1.py"]}
    mock_audit_data = {"risks": ["high"]}

    full_report_data = {
        "tokenomics_data": mock_tokenomics_data,
        "onchain_data": mock_onchain_data,
        "sentiment_data": mock_sentiment_data,
        "code_data": mock_code_data,
        "audit_data": mock_audit_data,
    }

    with respx.mock as respx_mock:
        respx_mock.post("https://api.openai.com/v1/chat/completions").side_effect = [
            Response(200, json={"choices": [{"message": {"content": "Mocked tokenomics text."}}]}),
            Response(200, json={"choices": [{"message": {"content": "Mocked on-chain text."}}]}),
            Response(200, json={"choices": [{"message": {"content": "Mocked sentiment text."}}]}),
            Response(200, json={"choices": [{"message": {"content": "Mocked code audit text."}}]}),
        ]

        response = await engine.generate_full_report(full_report_data)
        parsed_response = json.loads(response)

        assert "sections" in parsed_response
        assert len(parsed_response["sections"]) == 4

        section_ids = [s["section_id"] for s in parsed_response["sections"]]
        assert "tokenomics" in section_ids
        assert "onchain_metrics" in section_ids
        assert "social_sentiment" in section_ids
        assert "code_audit_summary" in section_ids

        for section in parsed_response["sections"]:
            if section["section_id"] == "tokenomics":
                assert "Mocked tokenomics text." in section["text"]
            elif section["section_id"] == "onchain_metrics":
                assert "Mocked on-chain text." in section["text"]
            elif section["section_id"] == "social_sentiment":
                assert "Mocked sentiment text." in section["text"]
            elif section["section_id"] == "code_audit_summary":
                assert "Mocked code audit text." in section["text"]
        
        assert respx_mock.calls.call_count == 4
