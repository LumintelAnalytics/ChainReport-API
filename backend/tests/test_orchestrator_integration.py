import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.core.orchestrator import create_orchestrator
from backend.app.services.report_service import in_memory_reports
from backend.app.core.config import settings

# Sample data for testing
SAMPLE_REPORT_ID = "test_report_123"
SAMPLE_TOKEN_ID = "ethereum"

@pytest.fixture(autouse=True)
def clear_in_memory_reports():
    """Clears in_memory_reports before each test."""
    in_memory_reports.clear()
    yield

@pytest.fixture
def mock_settings():
    """Mocks settings required for agent registration."""
    # Patch settings as it's imported in orchestrator.py
    with patch('backend.app.core.orchestrator.settings') as mock_orchestrator_settings:
        mock_orchestrator_settings.ONCHAIN_METRICS_URL = "http://mock-onchain-metrics.com"
        mock_orchestrator_settings.TOKENOMICS_URL = "http://mock-tokenomics.com"
        mock_orchestrator_settings.CODE_AUDIT_REPO_URL = "http://mock-code-audit.com/repo"
        mock_orchestrator_settings.AGENT_TIMEOUT = 5  # Shorter timeout for tests
        mock_orchestrator_settings.TEAM_PROFILE_URLS = {SAMPLE_TOKEN_ID: ["http://mock-team-profile.com"]}
        mock_orchestrator_settings.WHITEPAPER_TEXT_SOURCES = {SAMPLE_TOKEN_ID: "mock whitepaper text"}
        yield mock_orchestrator_settings

@pytest.mark.asyncio
async def test_orchestrator_full_integration_success(mock_settings):
    """
    Tests the full integration of the orchestrator with all agents
    executing successfully.
    """
    # Mock agent functions
    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics', new_callable=AsyncMock) as mock_fetch_onchain_metrics, \
         patch('backend.app.services.agents.onchain_agent.fetch_tokenomics', new_callable=AsyncMock) as mock_fetch_tokenomics, \
         patch('backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent.fetch_social_data', new_callable=AsyncMock) as mock_fetch_social_data, \
         patch('backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent.analyze_sentiment', new_callable=AsyncMock) as mock_analyze_sentiment, \
         patch('backend.app.services.agents.team_doc_agent.TeamDocAgent.scrape_team_profiles', new_callable=MagicMock) as mock_scrape_team_profiles, \
         patch('backend.app.services.agents.team_doc_agent.TeamDocAgent.analyze_whitepaper', new_callable=MagicMock) as mock_analyze_whitepaper, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.fetch_repo_metrics', new_callable=AsyncMock) as mock_fetch_repo_metrics, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.analyze_code_activity', new_callable=AsyncMock) as mock_analyze_code_activity, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.search_and_summarize_audit_reports', new_callable=AsyncMock) as mock_search_and_summarize_audit_reports:

        mock_fetch_onchain_metrics.return_value = {"onchain_metrics_data": "mocked"}
        mock_fetch_tokenomics.return_value = {"tokenomics_data": "mocked"}
        mock_fetch_social_data.return_value = {"social_data": "mocked"}
        mock_analyze_sentiment.return_value = {"overall_sentiment": "positive", "score": 0.8, "summary": "mocked sentiment"}
        mock_scrape_team_profiles.return_value = [{"team_member": "mocked"}]
        mock_analyze_whitepaper.return_value = {"whitepaper_summary": "mocked"}
        mock_fetch_repo_metrics.return_value = MagicMock(model_dump=lambda: {"repo_metrics": "mocked"})
        mock_analyze_code_activity.return_value = {"activity_analysis": "mocked"}
        mock_search_and_summarize_audit_reports.return_value = [{"audit_report": "mocked"}]

        in_memory_reports[SAMPLE_REPORT_ID] = {"status": "pending", "data": {}}
        orchestrator = create_orchestrator()
        result = await orchestrator.execute_agents_concurrently(SAMPLE_REPORT_ID, SAMPLE_TOKEN_ID)

        # Assertions for successful execution and aggregated output
        assert "onchain_metrics" in result
        assert "tokenomics" in result
        assert "social_sentiment" in result
        assert "team_documentation" in result
        assert "team_analysis" in result["team_documentation"]
        assert "whitepaper_summary" in result["team_documentation"]
        assert "code_audit" in result
        assert "code_metrics" in result["code_audit"]
        assert "audit_summary" in result["code_audit"]

        assert in_memory_reports[SAMPLE_REPORT_ID]["status"] == "completed"
        assert in_memory_reports[SAMPLE_REPORT_ID]["data"] == result

        # Verify agent calls
        mock_fetch_onchain_metrics.assert_called_once()
        mock_fetch_tokenomics.assert_called_once()
        mock_fetch_social_data.assert_called_once()
        mock_analyze_sentiment.assert_called_once()
        mock_scrape_team_profiles.assert_called_once()
        mock_analyze_whitepaper.assert_called_once()
        mock_fetch_repo_metrics.assert_called_once()
        mock_analyze_code_activity.assert_called_once()
        mock_search_and_summarize_audit_reports.assert_called_once()

@pytest.mark.asyncio
async def test_orchestrator_agent_timeout_handling(mock_settings):
    """
    Tests that the orchestrator handles agent timeouts gracefully.
    """
    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics', new_callable=AsyncMock) as mock_fetch_onchain_metrics, \
         patch('backend.app.services.agents.onchain_agent.fetch_tokenomics', new_callable=AsyncMock) as mock_fetch_tokenomics, \
         patch('backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent.fetch_social_data', new_callable=AsyncMock) as mock_fetch_social_data, \
         patch('backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent.analyze_sentiment', new_callable=AsyncMock) as mock_analyze_sentiment, \
         patch('backend.app.services.agents.team_doc_agent.TeamDocAgent.scrape_team_profiles', new_callable=MagicMock) as mock_scrape_team_profiles, \
         patch('backend.app.services.agents.team_doc_agent.TeamDocAgent.analyze_whitepaper', new_callable=MagicMock) as mock_analyze_whitepaper, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.fetch_repo_metrics', new_callable=AsyncMock) as mock_fetch_repo_metrics, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.analyze_code_activity', new_callable=AsyncMock) as mock_analyze_code_activity, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.search_and_summarize_audit_reports', new_callable=AsyncMock) as mock_search_and_summarize_audit_reports:

        # Make one agent timeout
        mock_fetch_onchain_metrics.side_effect = asyncio.TimeoutError

        # Configure other mock return values for success
        mock_fetch_tokenomics.return_value = {"tokenomics_data": "mocked"}
        mock_fetch_social_data.return_value = {"social_data": "mocked"}
        mock_analyze_sentiment.return_value = {"overall_sentiment": "positive", "score": 0.8, "details": "mocked sentiment"}
        mock_scrape_team_profiles.return_value = [{"team_member": "mocked"}]
        mock_analyze_whitepaper.return_value = {"whitepaper_summary": "mocked"}
        mock_fetch_repo_metrics.return_value = AsyncMock(model_dump=lambda: {"repo_metrics": "mocked"})
        mock_analyze_code_activity.return_value = {"activity_analysis": "mocked"}
        mock_search_and_summarize_audit_reports.return_value = [{"audit_report": "mocked"}]

        in_memory_reports[SAMPLE_REPORT_ID] = {"status": "pending", "data": {}}
        orchestrator = create_orchestrator()
        result = await orchestrator.execute_agents_concurrently(SAMPLE_REPORT_ID, SAMPLE_TOKEN_ID)

        # Assertions for timeout handling
        assert "onchain_metrics" in result
        assert "error" in result["onchain_metrics"]
        assert result["onchain_metrics"]["error"] == "Onchain metrics fetch timed out"
        assert in_memory_reports[SAMPLE_REPORT_ID]["status"] == "failed" # Overall status should be failed due to timeout

@pytest.mark.asyncio
async def test_orchestrator_agent_exception_handling(mock_settings):
    """
    Tests that the orchestrator handles agent exceptions gracefully.
    """
    with patch('backend.app.services.agents.onchain_agent.fetch_onchain_metrics', new_callable=AsyncMock) as mock_fetch_onchain_metrics, \
         patch('backend.app.services.agents.onchain_agent.fetch_tokenomics', new_callable=AsyncMock) as mock_fetch_tokenomics, \
         patch('backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent.fetch_social_data', new_callable=AsyncMock) as mock_fetch_social_data, \
         patch('backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent.analyze_sentiment', new_callable=AsyncMock) as mock_analyze_sentiment, \
         patch('backend.app.services.agents.team_doc_agent.TeamDocAgent.scrape_team_profiles', new_callable=MagicMock) as mock_scrape_team_profiles, \
         patch('backend.app.services.agents.team_doc_agent.TeamDocAgent.analyze_whitepaper', new_callable=MagicMock) as mock_analyze_whitepaper, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.fetch_repo_metrics', new_callable=AsyncMock) as mock_fetch_repo_metrics, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.analyze_code_activity', new_callable=AsyncMock) as mock_analyze_code_activity, \
         patch('backend.app.services.agents.code_audit_agent.CodeAuditAgent.search_and_summarize_audit_reports', new_callable=AsyncMock) as mock_search_and_summarize_audit_reports:

        # Make one agent raise an exception
        mock_fetch_tokenomics.side_effect = Exception("Mocked agent error")

        # Configure other mock return values for success
        mock_fetch_onchain_metrics.return_value = {"onchain_data": "mocked"}
        mock_fetch_social_data.return_value = {"social_data": "mocked"}
        mock_analyze_sentiment.return_value = {"overall_sentiment": "positive", "score": 0.8, "details": "mocked sentiment"}
        mock_scrape_team_profiles.return_value = [{"team_member": "mocked"}]
        mock_analyze_whitepaper.return_value = {"whitepaper_summary": "mocked"}
        mock_fetch_repo_metrics.return_value = AsyncMock(model_dump=lambda: {"repo_metrics": "mocked"})
        mock_analyze_code_activity.return_value = {"activity_analysis": "mocked"}
        mock_search_and_summarize_audit_reports.return_value = [{"audit_report": "mocked"}]

        in_memory_reports[SAMPLE_REPORT_ID] = {"status": "pending", "data": {}}
        orchestrator = create_orchestrator()
        result = await orchestrator.execute_agents_concurrently(SAMPLE_REPORT_ID, SAMPLE_TOKEN_ID)

        # Assertions for exception handling
        assert "tokenomics" in result
        assert "error" in result["tokenomics"]
        assert result["tokenomics"]["error"] == "Mocked agent error"
        assert in_memory_reports[SAMPLE_REPORT_ID]["status"] == "failed" # Overall status should be failed due to exception
