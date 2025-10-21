import pytest
import asyncio
from typing import Any, List, Union

from backend.app.core.orchestrator import AIOrchestrator

class MockAgent:
    def __init__(self, name: str, result: Any = None, exception: Exception = None):
        self.name = name
        self._result = result
        self._exception = exception

    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        if self._exception:
            raise self._exception
        return self._result

@pytest.mark.asyncio
async def test_execute_agents_tolerates_failures():
    orchestrator = AIOrchestrator()

    # Create mock agents, one of which will raise an exception
    agent1 = MockAgent("Agent1", result="Result1")
    agent2 = MockAgent("Agent2", exception=ValueError("Agent2 failed"))
    agent3 = MockAgent("Agent3", result="Result3")

    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)
    orchestrator.register_agent(agent3)

    results = await orchestrator.execute_agents()

    assert len(results) == 3
    assert results[0] == "Result1"
    assert isinstance(results[1], ValueError)
    assert str(results[1]) == "Agent2 failed"
    assert results[2] == "Result3"

@pytest.mark.asyncio
async def test_execute_agents_all_succeed():
    orchestrator = AIOrchestrator()

    agent1 = MockAgent("Agent1", result="Result1")
    agent2 = MockAgent("Agent2", result="Result2")

    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)

    results = await orchestrator.execute_agents()

    assert len(results) == 2
    assert results[0] == "Result1"
    assert results[1] == "Result2"

@pytest.mark.asyncio
async def test_execute_agents_empty_agents():
    orchestrator = AIOrchestrator()
    results = await orchestrator.execute_agents()
    assert results == []
