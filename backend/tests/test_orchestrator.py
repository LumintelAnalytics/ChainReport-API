import pytest
from unittest.mock import AsyncMock
from backend.app.core.orchestrator import Orchestrator, create_orchestrator
from backend.app.services.report_service import in_memory_reports


@pytest.fixture(autouse=True)
def clear_in_memory_reports():
    in_memory_reports.clear()
    yield
    in_memory_reports.clear()

@pytest.mark.asyncio
async def test_execute_agents_concurrently_success():
    orchestrator = Orchestrator()
    mock_agent_one = AsyncMock(return_value={"agent_one_result": "data1"})
    mock_agent_two = AsyncMock(return_value={"agent_two_result": "data2"})

    orchestrator.register_agent("AgentOne", mock_agent_one)
    orchestrator.register_agent("AgentTwo", mock_agent_two)

    report_id = "test_report_id_success"
    token_id = "test_token_id"

    # Initialize report in in_memory_reports as generate_report would
    in_memory_reports[report_id] = {"token_id": token_id, "status": "processing"}

    await orchestrator.execute_agents_concurrently(report_id, token_id)

    mock_agent_one.assert_called_once_with(report_id, token_id)
    mock_agent_two.assert_called_once_with(report_id, token_id)

    assert in_memory_reports[report_id]["status"] == "completed"
    assert "agent_results" in in_memory_reports[report_id]
    assert in_memory_reports[report_id]["agent_results"]["AgentOne"] == {"status": "completed", "data": {"agent_one_result": "data1"}}
    assert in_memory_reports[report_id]["agent_results"]["AgentTwo"] == {"status": "completed", "data": {"agent_two_result": "data2"}}

@pytest.mark.asyncio
async def test_execute_agents_concurrently_with_failure():
    orchestrator = Orchestrator()
    mock_agent_one = AsyncMock(return_value={"agent_one_result": "data1"})
    mock_agent_failing = AsyncMock(side_effect=Exception("Agent failed"))

    orchestrator.register_agent("AgentOne", mock_agent_one)
    orchestrator.register_agent("AgentFailing", mock_agent_failing)

    report_id = "test_report_id_failure"
    token_id = "test_token_id"

    # Initialize report in in_memory_reports as generate_report would
    in_memory_reports[report_id] = {"token_id": token_id, "status": "processing"}

    await orchestrator.execute_agents_concurrently(report_id, token_id)

    mock_agent_one.assert_called_once_with(report_id, token_id)
    mock_agent_failing.assert_called_once_with(report_id, token_id)

    assert in_memory_reports[report_id]["status"] == "partial_success"
    assert "agent_results" in in_memory_reports[report_id]
    assert in_memory_reports[report_id]["agent_results"]["AgentOne"] == {"status": "completed", "data": {"agent_one_result": "data1"}}
    assert in_memory_reports[report_id]["agent_results"]["AgentFailing"]["status"] == "failed"
    assert "error" in in_memory_reports[report_id]["agent_results"]["AgentFailing"]
    assert "Agent failed" in in_memory_reports[report_id]["agent_results"]["AgentFailing"]["error"]

def test_get_agents_returns_copy():
    orch = Orchestrator()
    def func(): pass
    orch.register_agent('a', func)
    got = orch.get_agents()
    got.clear()
    assert 'a' in orch.get_agents()

def test_create_orchestrator_no_dummy_by_default():
    orch = create_orchestrator()
    assert 'dummy_agent' not in orch.get_agents()

def test_create_orchestrator_with_dummy():
    orch = create_orchestrator(register_dummy=True)
    assert 'dummy_agent' in orch.get_agents()
    # Ensure it's callable
    assert callable(orch.get_agents()['dummy_agent'])