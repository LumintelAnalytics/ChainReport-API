import pytest
from unittest.mock import AsyncMock
from backend.app.core.orchestrator import Orchestrator, create_orchestrator
from backend.app.db.models.report_state import ReportStatusEnum, ReportState
from backend.app.db.repositories.report_repository import ReportRepository


@pytest.fixture
def mock_session_factory():
    return AsyncMock()


@pytest.mark.asyncio
async def test_execute_agents_success(mock_session_factory):
    orchestrator = Orchestrator(mock_session_factory)
    orchestrator.report_repository.get_report_by_id = AsyncMock(return_value=ReportState(report_id="test_report_id", status=ReportStatusEnum.RUNNING))
    orchestrator.report_repository.update_partial = AsyncMock(return_value=None)
    mock_agent_one = AsyncMock(return_value={"status": "completed", "data": {"agent_one_result": "data1"}})
    mock_agent_two = AsyncMock(return_value={"status": "completed", "data": {"agent_two_result": "data2"}})

    orchestrator.register_agent("AgentOne", mock_agent_one)
    orchestrator.register_agent("AgentTwo", mock_agent_two)

    report_id = "test_report_id"
    token_id = "test_token_id"

    await orchestrator.execute_agents(report_id, token_id)

    mock_agent_one.assert_called_once_with(report_id, token_id)
    mock_agent_two.assert_called_once_with(report_id, token_id)

    orchestrator.report_repository.update_partial.assert_called_with(
        report_id,
        {"status": ReportStatusEnum.AGENTS_COMPLETED}
    )

@pytest.mark.asyncio
async def test_execute_agents_with_failure(mock_session_factory):
    orchestrator = Orchestrator(mock_session_factory)
    report_id = "test_report_id"
    token_id = "test_token_id"

    mock_agent_one = AsyncMock(return_value={"status": "completed", "data": {"agent_one_result": "data1"}})
    mock_agent_failing = AsyncMock(side_effect=Exception("Agent failed"))

    orchestrator.register_agent("AgentOne", mock_agent_one)
    orchestrator.register_agent("AgentFailing", mock_agent_failing)

    # Set up mock to return an existing report with no errors initially
    orchestrator.report_repository.get_report_by_id = AsyncMock(return_value=ReportState(
        report_id=report_id, status=ReportStatusEnum.RUNNING, errors={}
    ))
    orchestrator.report_repository.update_partial = AsyncMock(return_value=None)

    await orchestrator.execute_agents(report_id, token_id)

    mock_agent_one.assert_called_once_with(report_id, token_id)
    mock_agent_failing.assert_called_once_with(report_id, token_id)

    orchestrator.report_repository.update_partial.assert_called_with(
        report_id,
        {"status": ReportStatusEnum.AGENTS_FAILED, "errors": {"AgentFailing": True}}
    )


def test_get_agents_returns_copy(mock_session_factory):
    orch = Orchestrator(mock_session_factory)
    def func(): pass
    orch.register_agent('a', func)
    got = orch.get_agents()
    got.clear()
    assert 'a' in orch.get_agents()


@pytest.mark.asyncio
async def test_create_orchestrator_no_dummy_by_default():
    mock_session_factory = AsyncMock()
    orch = await create_orchestrator(session_factory=mock_session_factory)
    assert 'dummy_agent' not in orch.get_agents()


@pytest.mark.asyncio
async def test_create_orchestrator_with_dummy():
    mock_session_factory = AsyncMock()
    orch = await create_orchestrator(register_dummy=True, session_factory=mock_session_factory)
    assert 'dummy_agent' in orch.get_agents()
    # Ensure it's callable
    assert callable(orch.get_agents()['dummy_agent'])