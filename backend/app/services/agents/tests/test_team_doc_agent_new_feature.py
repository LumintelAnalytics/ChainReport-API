import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_generate_team_doc_text(mocker):
    # Mock LLMClient class and its instance
    mock_llm_client_class = mocker.patch('backend.app.services.agents.team_doc_agent.LLMClient')
    mock_llm_client_instance = AsyncMock()
    mock_llm_client_class.return_value.__aenter__.return_value = mock_llm_client_instance

    # Import TeamDocAgent after patching LLMClient
    from backend.app.services.agents.team_doc_agent import TeamDocAgent
    agent = TeamDocAgent()

    # Sample data
    team_data = [
        {"name": "John Doe", "title": "CEO", "biography": "Experienced leader in blockchain.", "credentials_verified": True},
        {"name": "Jane Smith", "title": "CTO", "biography": "Expert in smart contract development.", "credentials_verified": True}
    ]
    doc_data = {
        "project_timelines": [{"event": "Phase 1 Completion", "date": "Q1 2026"}],
        "roadmap_items": ["Mainnet Launch"],
        "analysis_summary": "Comprehensive documentation available."
    }

    # Mock LLM responses
    mock_llm_client_instance.generate_text.side_effect = [
        {"choices": [{"message": {"content": "Summary of team roles."}}]}, # Corrected
        {"choices": [{"message": {"content": "Summary of team experience."}}]}, # Corrected
        {"choices": [{"message": {"content": "Summary of team credibility."}}]}, # Corrected
        {"choices": [{"message": {"content": "Summary of documentation strength."}}]}, # Corrected
    ]

    expected_output_parts = [
        "### Team Roles and Responsibilities\nSummary of team roles.\n\n",
        "### Team Experience and Expertise\nSummary of team experience.\n\n",
        "### Team Credibility\nSummary of team credibility.\n\n",
        "### Documentation Strength\nSummary of documentation strength.\n\n"
    ]
    expected_output = "".join(expected_output_parts)

    result = await agent.generate_team_doc_text(team_data, doc_data)

    assert result == expected_output
    assert mock_llm_client_instance.generate_text.call_count == 4

    # Verify prompts were called (basic check)
    calls = mock_llm_client_instance.generate_text.call_args_list
    assert len(calls) == 4
    # Further assertions could check the content of the prompts if needed, but for now, just checking call count is sufficient.
