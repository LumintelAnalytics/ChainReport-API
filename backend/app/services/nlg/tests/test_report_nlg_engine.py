import pytest
import json
from unittest.mock import AsyncMock, patch
from backend.app.services.nlg.report_nlg_engine import ReportNLGEngine
from backend.app.services.nlg.llm_client import LLMClient
from backend.app.services.nlg.prompt_templates import get_template, fill_template

# Mock the LLMClient for all tests in this module
@pytest.fixture
def mock_llm_client():
    with patch('backend.app.services.nlg.report_nlg_engine.LLMClient', autospec=True) as MockLLMClient:
        mock_instance = MockLLMClient.return_value
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock_instance.generate_text = AsyncMock()
        yield mock_instance

@pytest.fixture
def report_nlg_engine():
    return ReportNLGEngine()

@pytest.mark.asyncio
async def test_generate_code_audit_text_success(mock_llm_client, report_nlg_engine):
    mock_llm_client.generate_text.return_value = {
        "choices": [{"message": {"content": "This is a generated code audit summary."}}]
    }
    code_data = {"lines": 100, "files": 10}
    audit_data = [{"finding": "High severity bug"}]
    
    result = await report_nlg_engine.generate_code_audit_text(code_data, audit_data)
    
    expected_output = json.dumps({
        "section_id": "code_audit_summary",
        "text": "This is a generated code audit summary."
    })
    assert result == expected_output
    mock_llm_client.generate_text.assert_called_once()
    
    # Validate prompt correctness
    expected_template = get_template("code_audit_summary")
    expected_prompt = fill_template(
        expected_template,
        code_data=json.dumps(code_data, indent=2),
        audit_data=json.dumps(audit_data, indent=2)
    )
    mock_llm_client.generate_text.assert_called_with(expected_prompt)

@pytest.mark.asyncio
async def test_generate_code_audit_text_missing_data(report_nlg_engine):
    result = await report_nlg_engine.generate_code_audit_text({}, [])
    expected_output = json.dumps({
        "section_id": "code_audit_summary",
        "text": "Code audit and repository data are not available at this time. Please check back later for updates."
    })
    assert result == expected_output

@pytest.mark.asyncio
async def test_generate_code_audit_text_empty_llm_response(mock_llm_client, report_nlg_engine):
    mock_llm_client.generate_text.return_value = {
        "choices": [{"message": {"content": ""}}]
    }
    code_data = {"lines": 100}
    audit_data = [{"finding": "Low"}]
    
    result = await report_nlg_engine.generate_code_audit_text(code_data, audit_data)
    expected_output = json.dumps({
        "section_id": "code_audit_summary",
        "text": "Failed to generate code audit summary due to an internal error. Please try again later."
    })
    assert result == expected_output

@pytest.mark.asyncio
async def test_generate_code_audit_text_llm_exception(mock_llm_client, report_nlg_engine):
    mock_llm_client.generate_text.side_effect = Exception("LLM connection error")
    code_data = {"lines": 100}
    audit_data = [{"finding": "Low"}]
    
    result = await report_nlg_engine.generate_code_audit_text(code_data, audit_data)
    expected_output = json.dumps({
        "section_id": "code_audit_summary",
        "text": "Failed to generate code audit summary due to an internal error. Please try again later."
    })
    assert result == expected_output

@pytest.mark.asyncio
async def test_generate_team_documentation_text_success(mock_llm_client, report_nlg_engine):
    mock_llm_client.generate_text.return_value = {
        "choices": [{"message": {"content": "This is a generated team documentation summary."}}]
    }
    raw_data = {"team_analysis": ["Strong team"], "whitepaper_summary": {"version": "1.0"}}
    
    result = await report_nlg_engine.generate_team_documentation_text(raw_data)
    
    expected_output = json.dumps({
        "section_id": "team_documentation",
        "text": "This is a generated team documentation summary."
    })
    assert result == expected_output
    mock_llm_client.generate_text.assert_called_once()
    
    # Validate prompt correctness
    expected_template = get_template("team_documentation")
    expected_prompt = fill_template(
        expected_template,
        team_analysis=json.dumps(raw_data["team_analysis"], indent=2),
        whitepaper_summary=json.dumps(raw_data["whitepaper_summary"], indent=2)
    )
    mock_llm_client.generate_text.assert_called_with(expected_prompt)

@pytest.mark.asyncio
async def test_generate_team_documentation_text_missing_data(report_nlg_engine):
    result = await report_nlg_engine.generate_team_documentation_text({})
    expected_output = json.dumps({
        "section_id": "team_documentation",
        "text": "Team and documentation data is not available at this time. Please check back later for updates."
    })
    assert result == expected_output

@pytest.mark.asyncio
async def test_generate_team_documentation_text_empty_llm_response(mock_llm_client, report_nlg_engine):
    mock_llm_client.generate_text.return_value = {
        "choices": [{"message": {"content": ""}}]
    }
    raw_data = {"team_analysis": ["Strong team"]}
    
    result = await report_nlg_engine.generate_team_documentation_text(raw_data)
    expected_output = json.dumps({
        "section_id": "team_documentation",
        "text": "Failed to generate team and documentation summary due to an internal error. Please try again later."
    })
    assert result == expected_output

@pytest.mark.asyncio
async def test_generate_team_documentation_text_llm_exception(mock_llm_client, report_nlg_engine):
    mock_llm_client.generate_text.side_effect = Exception("LLM connection error")
    raw_data = {"team_analysis": ["Strong team"]}
    
    result = await report_nlg_engine.generate_team_documentation_text(raw_data)
    expected_output = json.dumps({
        "section_id": "team_documentation",
        "text": "Failed to generate team and documentation summary due to an internal error. Please try again later."
    })
    assert result == expected_output
