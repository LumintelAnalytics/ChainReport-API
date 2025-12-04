import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
from freezegun import freeze_time

from backend.app.core.orchestrator import create_orchestrator
from backend.app.core.logger import orchestrator_logger
from backend.app.db.models.report_state import ReportState, ReportStatusEnum

# Mock database session factory
@pytest.fixture
def mock_session_factory():
    mock_session = AsyncMock()
    return lambda: mock_session

@pytest.fixture
def mock_settings():
    with patch("backend.app.core.config.settings") as mock_app_settings:
        mock_app_settings.ONCHAIN_METRICS_URL = "http://mock-onchain.com"
        mock_app_settings.TOKENOMICS_URL = "http://mock-tokenomics.com"
        mock_app_settings.CODE_AUDIT_REPO_URL = "http://mock-code-audit.com"
        mock_app_settings.TEAM_PROFILE_URLS = {"test_token_id": ["http://mock-team-profile.com"]}
        mock_app_settings.WHITEPAPER_TEXT_SOURCES = {"test_token_id": "http://mock-whitepaper.com"}
        mock_app_settings.AGENT_TIMEOUT = 10 # Set a reasonable timeout for tests
        mock_app_settings.DEBUG = True # Enable debug for full stack traces
        yield mock_app_settings

# Mock agent dependencies
@pytest.fixture(autouse=True)
def mock_agent_dependencies():
    with (
        patch("backend.app.services.agents.onchain_agent.fetch_onchain_metrics", new_callable=AsyncMock) as mock_fetch_metrics,
        patch("backend.app.services.agents.onchain_agent.fetch_tokenomics", new_callable=AsyncMock) as mock_fetch_tokenomics,
        patch("backend.app.services.agents.social_sentiment_agent.SocialSentimentAgent", autospec=True) as MockSocialAgent,
        patch("backend.app.services.agents.team_doc_agent.TeamDocAgent", autospec=True) as MockTeamDocAgent,
        patch("backend.app.services.agents.code_audit_agent.CodeAuditAgent", autospec=True) as MockCodeAuditAgent
    ):
        
        # Onchain Agent mocks
        mock_fetch_metrics.return_value = {"status": "completed", "data": {"metrics": "mocked"}}
        mock_fetch_tokenomics.return_value = {"status": "completed", "data": {"tokenomics": "mocked"}}

        # Social Sentiment Agent mocks
        mock_social_agent_instance = MockSocialAgent.return_value
        mock_social_agent_instance.fetch_social_data.return_value = {"twitter": ["mock_tweet"], "reddit": ["mock_reddit"], "news": ["mock_news"]}
        mock_social_agent_instance.analyze_sentiment.return_value = {"overall_sentiment": "positive", "score": 0.8, "details": "mocked sentiment"}

        # Team Doc Agent mocks
        mock_team_doc_agent_instance = MockTeamDocAgent.return_value
        mock_team_doc_agent_instance.scrape_team_profiles.return_value = [{"name": "mock_team_member"}]
        mock_team_doc_agent_instance.analyze_whitepaper.return_value = {"summary": "mocked whitepaper summary"}

        # Code Audit Agent mocks
        mock_code_audit_agent_instance = MockCodeAuditAgent.return_value
        mock_code_audit_agent_instance.__aenter__.return_value = mock_code_audit_agent_instance # For async with
        mock_code_audit_agent_instance.__aexit__.return_value = None
        mock_code_audit_agent_instance.fetch_repo_metrics.return_value.model_dump.return_value = {"metrics": "mocked"}
        mock_code_audit_agent_instance.analyze_code_activity.return_value = {"activity": "mocked"}
        mock_code_audit_agent_instance.search_and_summarize_audit_reports.return_value = [{"audit": "mocked"}]

        yield

@pytest.fixture
def mock_redis_client():
    with patch("backend.app.cache.redis_client.redis_client", autospec=True) as mock_redis:
        mock_redis.set_cache.return_value = None
        mock_redis.get_cache.return_value = None
        mock_redis.delete_cache.return_value = None
        yield mock_redis

@pytest.mark.asyncio
async def test_orchestrator_logging(caplog, mock_session_factory, mock_settings, mock_agent_dependencies):
    with caplog.at_level("INFO"):
        orchestrator = await create_orchestrator(session_factory=mock_session_factory, register_dummy=True)
        report_id = "log_test_report"
        token_id = "log_test_token"
        await orchestrator.execute_agents(report_id, token_id)

        assert len(caplog.records) > 0
        assert any(f"Dummy agent received report_id: {report_id}" in r.message for r in caplog.records)
        assert any(f"Calling Onchain Data Agent for report_id: {report_id}" in r.message for r in caplog.records)
        assert any(f"Calling Social Sentiment Agent for report_id: {report_id}" in r.message for r in caplog.records)
        assert any(f"Calling Team and Documentation Agent for report_id: {report_id}" in r.message for r in caplog.records)
        assert any(f"Calling Code/Audit Agent for report_id: {report_id}" in r.message for r in caplog.records)

@pytest.mark.asyncio
async def test_orchestrator_error_capturing(caplog, mock_session_factory, mock_settings, mock_agent_dependencies):
    with patch("backend.app.core.error_utils.capture_exception", new_callable=AsyncMock) as mock_capture_exception:
        orchestrator = await create_orchestrator(session_factory=mock_session_factory)

        # Create a mock ReportState for the orchestrator to retrieve
        mock_report_state_for_error = ReportState(
            report_id="error_test_report",
            status=ReportStatusEnum.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            errors={},
            timing_alerts=[]
        )
        orchestrator.report_repository.get_report_by_id = AsyncMock(return_value=mock_report_state_for_error)
        orchestrator.report_repository.update_partial = AsyncMock()

        async def failing_agent(report_id: str, token_id: str):
            raise ValueError("Agent failed due to a test error.")

        orchestrator.register_agent("failing_agent", failing_agent)

        report_id = "error_test_report"
        token_id = "error_test_token"
        
        with caplog.at_level("ERROR"):
            results = await orchestrator.execute_agents(report_id, token_id)

            assert "failing_agent" in results
            assert results["failing_agent"]["status"] == "failed"
            assert "error" in results["failing_agent"]

            mock_capture_exception.assert_called_once()
            assert mock_capture_exception.call_args[0][0].args[0] == "Agent failed due to a test error."
            assert mock_capture_exception.call_args[0][1]["agent_name"] == "failing_agent"
            assert mock_capture_exception.call_args[0][1]["report_id"] == report_id

            orchestrator.report_repository.update_partial.assert_called_once()
            call_args = orchestrator.report_repository.update_partial.call_args
            assert call_args[0][0] == report_id
            assert call_args[0][1]["status"] == ReportStatusEnum.AGENTS_FAILED
            assert "failing_agent" in call_args[0][1]["errors"]
            assert call_args[0][1]["errors"]["failing_agent"] is True

            assert any("Agent failing_agent failed for report error_test_report" in r.message for r in caplog.records)

@pytest.mark.asyncio
@freeze_time("2025-01-01 12:00:00")
async def test_time_tracker_slow_operation(caplog, mock_session_factory, mock_redis_client, mock_settings, mock_agent_dependencies):
    from backend.app.core import time_tracker
    
    report_id = "slow_report"

    # Create a mock ReportState for the orchestrator to retrieve
    mock_report_state_for_timer = ReportState(
        report_id="slow_report",
        status=ReportStatusEnum.PENDING,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        errors={},
        timing_alerts=[]
    )
    # Patch the ReportRepository within the time_tracker.finish_timer scope
    with patch("backend.app.core.time_tracker.ReportRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        mock_repo_instance.get_report_by_id = AsyncMock(return_value=mock_report_state_for_timer)
        mock_repo_instance.update_timing_alerts = AsyncMock()

        # Mock Redis to simulate start_timer
        mock_redis_client.get_cache.return_value = datetime.now().isoformat().encode('utf-8')

        # Start timer explicitly (orchestrator doesn't call this directly)
        time_tracker.start_timer(report_id)
        mock_redis_client.set_cache.assert_called_once_with(
            f"report_timer:{report_id}",
            datetime.now().isoformat(),
            ttl=3600 * 24
        )

        # Advance time by more than 5 minutes for the finish_timer call
        with freeze_time("2025-01-01 12:05:01", tick=True): # 5 minutes and 1 second later
            with caplog.at_level("WARNING"):
                # Call execute_agents, which will internally lead to finish_timer being called in a real scenario
                # For this test, we are explicitly calling finish_timer to test its logic
                duration = await time_tracker.finish_timer(report_id, mock_session_factory())

                assert duration > 300
                mock_redis_client.get_cache.assert_called_with(f"report_timer:{report_id}")
                mock_redis_client.delete_cache.assert_called_with(f"report_timer:{report_id}")

                # Verify warning log
                assert any(f"Report {report_id} processing time exceeded 5 minutes" in r.message for r in caplog.records)

                # Verify that update_timing_alerts was called on ReportRepository
                mock_repo_instance.update_timing_alerts.assert_called_once()
                call_args = mock_repo_instance.update_timing_alerts.call_args
                assert call_args[0][0] == report_id
                timing_alerts = call_args[0][1]
                assert len(timing_alerts) == 1
                assert "Report processing time exceeded 5 minutes" in timing_alerts[0]["message"]
                assert timing_alerts[0]["threshold"] == "5 minutes"
