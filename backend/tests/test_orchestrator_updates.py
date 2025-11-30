import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.core.orchestrator import Orchestrator
from backend.app.db.models.report_state import ReportStatusEnum, ReportState
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.repositories.report_repository import ReportRepository

# Mock ReportState object
class MockReportState:
    def __init__(self, report_id, status, errors=None):
        self.report_id = report_id
        self.status = status
        self.errors = errors if errors is not None else {}
        self.partial_agent_output = {}

@pytest.fixture
def mock_session_factory():
    return MagicMock(spec=AsyncSession)

@pytest.fixture
def mock_report_repository(mock_session_factory):
    repo = ReportRepository(mock_session_factory)
    repo.get_report_by_id = AsyncMock()
    repo.update_partial = AsyncMock()
    return repo

@pytest.fixture
def orchestrator(mock_session_factory, mock_report_repository):
    orch = Orchestrator(mock_session_factory)
    orch.report_repository = mock_report_repository
    return orch

@pytest.mark.asyncio
async def test_execute_agents_success_updates_status(orchestrator, mock_report_repository):
    report_id = "test_report_id_success"
    token_id = "test_token_id"

    # Mock a successful report retrieval
    mock_report = MockReportState(report_id, ReportStatusEnum.RUNNING)
    mock_report_repository.get_report_by_id.return_value = mock_report

    # Mock agents to succeed
    mock_agent_one = AsyncMock(return_value={"agent_one_result": "data1"})
    orchestrator.register_agent("AgentOne", mock_agent_one)

    await orchestrator.execute_agents(report_id, token_id)

    mock_report_repository.get_report_by_id.assert_called_with(report_id)
    mock_report_repository.update_partial.assert_called_with(
        report_id,
        {"status": ReportStatusEnum.AGENTS_COMPLETED}
    )
    mock_agent_one.assert_called_once_with(report_id, token_id)

@pytest.mark.asyncio
async def test_execute_agents_failure_updates_status_and_errors(orchestrator, mock_report_repository):
    report_id = "test_report_id_failure"
    token_id = "test_token_id"

    # Mock a report retrieval with initial status
    mock_report = MockReportState(report_id, ReportStatusEnum.RUNNING)
    mock_report_repository.get_report_by_id.return_value = mock_report

    # Mock one agent to fail
    mock_agent_one = AsyncMock(side_effect=Exception("Agent failed"))
    orchestrator.register_agent("AgentOne", mock_agent_one)

    await orchestrator.execute_agents(report_id, token_id)

    mock_report_repository.get_report_by_id.assert_called_with(report_id)
    mock_report_repository.update_partial.assert_called_with(
        report_id,
        {"status": ReportStatusEnum.AGENTS_FAILED, "errors": {"AgentOne": True}}
    )
    mock_agent_one.assert_called_once_with(report_id, token_id)

@pytest.mark.asyncio
async def test_execute_agents_failure_report_not_found_raises_runtime_error(orchestrator, mock_report_repository):
    report_id = "test_report_id_failure_no_report"
    token_id = "test_token_id"

    # Mock report not found
    mock_report_repository.get_report_by_id.return_value = None

    # Mock one agent to fail
    mock_agent_one = AsyncMock(side_effect=Exception("Agent failed"))
    orchestrator.register_agent("AgentOne", mock_agent_one)

    with pytest.raises(RuntimeError) as excinfo:
        await orchestrator.execute_agents(report_id, token_id)

    assert f"Report {report_id} not found when attempting to update with agent errors. Errors detected: {{'AgentOne': True}}" in str(excinfo.value)
    mock_report_repository.get_report_by_id.assert_called_once_with(report_id)
    mock_report_repository.update_partial.assert_not_called()
    mock_agent_one.assert_called_once_with(report_id, token_id)

@pytest.mark.asyncio
async def test_execute_agents_success_report_not_found_logs_warning(orchestrator, mock_report_repository, caplog):
    report_id = "test_report_id_success_no_report"
    token_id = "test_token_id"

    # Mock report not found
    mock_report_repository.get_report_by_id.return_value = None

    # Mock agents to succeed
    mock_agent_one = AsyncMock(return_value={"agent_one_result": "data1"})
    orchestrator.register_agent("AgentOne", mock_agent_one)

    await orchestrator.execute_agents(report_id, token_id)

    mock_report_repository.get_report_by_id.assert_called_with(report_id)
    mock_report_repository.update_partial.assert_not_called()
    mock_agent_one.assert_called_once_with(report_id, token_id)

    assert f"Report {report_id} not found when attempting to update with AGENTS_COMPLETED status." in caplog.text
