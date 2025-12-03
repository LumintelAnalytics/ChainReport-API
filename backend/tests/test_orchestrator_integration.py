import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.core.orchestrator import create_orchestrator

# Sample data for testing
SAMPLE_REPORT_ID = "test_report_123"
SAMPLE_TOKEN_ID = "ethereum"

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
    with patch('backend.app.core.orchestrator.fetch_onchain_metrics', new_callable=AsyncMock) as mock_fetch_onchain_metrics, \
         patch('backend.app.core.orchestrator.fetch_tokenomics', new_callable=AsyncMock) as mock_fetch_tokenomics, \
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

        # Setup mock for ReportRepository and its interactions
        from backend.app.db.models.report_state import ReportStatusEnum

        mock_session = AsyncMock()
        # Mock the async context manager for the session factory
        mock_session_factory = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)))
        
        orchestrator = await create_orchestrator(session_factory=mock_session_factory)
        mock_report_repository = orchestrator.report_repository

        # Mock initial report state (PENDING)
        mock_report_state_pending = AsyncMock()
        mock_report_state_pending.report_id = SAMPLE_REPORT_ID
        mock_report_state_pending.status = ReportStatusEnum.PENDING
        mock_report_state_pending.partial_agent_output = {}

        # Mock final report state (COMPLETED)
        mock_report_state_completed = AsyncMock()
        mock_report_state_completed.report_id = SAMPLE_REPORT_ID
        mock_report_state_completed.status = ReportStatusEnum.AGENTS_COMPLETED
        mock_report_state_completed.partial_agent_output = {} # Will be updated

        # Configure get_report_by_id to return pending then completed after update
        mock_report_repository.get_report_by_id.side_effect = [
            mock_report_state_pending, # First call during initial status check
            mock_report_state_completed # Second call after update_partial for AGENTS_COMPLETED
        ]
        mock_report_repository.update_partial.return_value = mock_report_state_completed # Ensure update returns something

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

        # Verify report repository interactions
        mock_report_repository.get_report_by_id.assert_called_with(SAMPLE_REPORT_ID)
        # Check that update_partial was called with AGENTS_COMPLETED status
        assert mock_report_repository.update_partial.call_count > 0
        update_call_args = mock_report_repository.update_partial.call_args_list[-1].args
        assert update_call_args[0] == SAMPLE_REPORT_ID
        assert update_call_args[1].get("status") == ReportStatusEnum.AGENTS_COMPLETED

@pytest.mark.asyncio
async def test_orchestrator_agent_timeout_handling(mock_settings):
    """
    Tests that the orchestrator handles agent timeouts gracefully.
    """
    with patch('backend.app.core.orchestrator.fetch_onchain_metrics', new_callable=AsyncMock) as mock_fetch_onchain_metrics, \
         patch('backend.app.core.orchestrator.fetch_tokenomics', new_callable=AsyncMock) as mock_fetch_tokenomics, \
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

        # Setup mock for ReportRepository and its interactions
        from backend.app.db.models.report_state import ReportStatusEnum
        mock_session = AsyncMock()
        mock_session_factory = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)))

        orchestrator = await create_orchestrator(session_factory=mock_session_factory)
        mock_report_repository = orchestrator.report_repository

        # Mock initial report state (PENDING)
        mock_report_state_pending = AsyncMock()
        mock_report_state_pending.report_id = SAMPLE_REPORT_ID
        mock_report_state_pending.status = ReportStatusEnum.PENDING
        mock_report_state_pending.partial_agent_output = {}

        # Mock failed report state
        mock_report_state_failed = AsyncMock()
        mock_report_state_failed.report_id = SAMPLE_REPORT_ID
        mock_report_state_failed.status = ReportStatusEnum.AGENTS_FAILED
        mock_report_state_failed.partial_agent_output = {}
        mock_report_state_failed.errors = {"onchain_data_agent": True}

        # Configure get_report_by_id to return pending then failed after update
        mock_report_repository.get_report_by_id.side_effect = [
            mock_report_state_pending, # First call during initial status check
            mock_report_state_failed # Second call after update_partial for AGENTS_FAILED
        ]
        mock_report_repository.update_partial.return_value = mock_report_state_failed

        result = await orchestrator.execute_agents_concurrently(SAMPLE_REPORT_ID, SAMPLE_TOKEN_ID)

        # Assertions for timeout handling
        assert "onchain_metrics" not in result
        mock_report_repository.get_report_by_id.assert_called_with(SAMPLE_REPORT_ID)
        # Check that update_partial was called with AGENTS_FAILED status and error details
        assert mock_report_repository.update_partial.call_count > 0
        update_call_args = mock_report_repository.update_partial.call_args_list[-1].args
        assert update_call_args[0] == SAMPLE_REPORT_ID
        assert update_call_args[1].get("status") == ReportStatusEnum.AGENTS_FAILED
        assert "onchain_data_agent" in update_call_args[1].get("errors", {})
@pytest.mark.asyncio
async def test_orchestrator_agent_exception_handling(mock_settings):
    """
    Tests that the orchestrator handles agent exceptions gracefully.
    """
    with patch('backend.app.core.orchestrator.fetch_onchain_metrics', new_callable=AsyncMock) as mock_fetch_onchain_metrics, \
         patch('backend.app.core.orchestrator.fetch_tokenomics', new_callable=AsyncMock) as mock_fetch_tokenomics, \
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

        # Setup mock for ReportRepository and its interactions
        from backend.app.db.models.report_state import ReportStatusEnum
        mock_session = AsyncMock()
        mock_session_factory = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session)))

        orchestrator = await create_orchestrator(session_factory=mock_session_factory)
        mock_report_repository = orchestrator.report_repository

        # Mock initial report state (PENDING)
        mock_report_state_pending = AsyncMock()
        mock_report_state_pending.report_id = SAMPLE_REPORT_ID
        mock_report_state_pending.status = ReportStatusEnum.PENDING
        mock_report_state_pending.partial_agent_output = {}

        # Mock failed report state
        mock_report_state_failed = AsyncMock()
        mock_report_state_failed.report_id = SAMPLE_REPORT_ID
        mock_report_state_failed.status = ReportStatusEnum.AGENTS_FAILED
        mock_report_state_failed.partial_agent_output = {}
        mock_report_state_failed.errors = {"onchain_data_agent": True}

        # Configure get_report_by_id to return pending then failed after update
        mock_report_repository.get_report_by_id.side_effect = [
            mock_report_state_pending, # First call during initial status check
            mock_report_state_failed # Second call after update_partial for AGENTS_FAILED
        ]
        mock_report_repository.update_partial.return_value = mock_report_state_failed

        result = await orchestrator.execute_agents_concurrently(SAMPLE_REPORT_ID, SAMPLE_TOKEN_ID)

        # Assertions for exception handling
        assert "tokenomics" not in result
        mock_report_repository.get_report_by_id.assert_called_with(SAMPLE_REPORT_ID)
        # Check that update_partial was called with AGENTS_FAILED status and error details
        assert mock_report_repository.update_partial.call_count > 0
        update_call_args = mock_report_repository.update_partial.call_args_list[-1].args
        assert update_call_args[0] == SAMPLE_REPORT_ID
        assert update_call_args[1].get("status") == ReportStatusEnum.AGENTS_FAILED
        assert "onchain_data_agent" in update_call_args[1].get("errors", {})