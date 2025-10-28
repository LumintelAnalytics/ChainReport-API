import asyncio
import logging
from typing import Callable, Dict, Any, List
from backend.app.services.report_service import in_memory_reports

logger = logging.getLogger(__name__)

async def dummy_agent(report_id: str, token_id: str) -> Dict[str, Any]:
    """
    A dummy agent for testing purposes.
    """
    logger.info("Dummy agent received report_id: %s, token_id: %s", report_id, token_id)
    await asyncio.sleep(1)  # Simulate some async work
    return {"dummy_data": f"Processed by dummy agent for {report_id}"}

class AIOrchestrator:
    """
    Base class for coordinating multiple AI agents.
    Designed to handle parallel asynchronous agent calls.
    """

    def __init__(self):
        self._agents: Dict[str, Callable] = {}

    def register_agent(self, name: str, agent_func: Callable):
        """
        Registers an AI agent with the orchestrator.
        Args:
            name (str): The name of the agent.
            agent_func (Callable): The asynchronous function representing the agent.
        """
        self._agents[name] = agent_func

    def get_agents(self) -> Dict[str, Callable]:
        """
        Returns the dictionary of registered AI agents.
        Returns:
            Dict[str, Callable]: A dictionary where keys are agent names and values are agent functions.
        """
        return self._agents

    async def execute_agents(self, report_id: str, token_id: str) -> Dict[str, Any]:
        tasks = {name: asyncio.create_task(agent_func(report_id, token_id)) for name, agent_func in self._agents.items()}
        results = {}

        for name, task in tasks.items():
            try:
                result = await asyncio.wait_for(task, timeout=10) # Added timeout
                results[name] = {"status": "completed", "data": result}
            except asyncio.TimeoutError: # Handle timeout specifically
                logger.exception("Agent %s timed out for report %s", name, report_id)
                results[name] = {"status": "failed", "error": "Agent timed out"}
            except Exception as e:
                logger.exception("Agent %s failed for report %s", name, report_id)
                results[name] = {"status": "failed", "error": str(e)}
        return results

    def aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregates the results from the executed AI agents.
        Args:
            results (dict): A dictionary of results from the executed agents.
        Returns:
            The aggregated result.
        """
        return {"agent_results": results}

class Orchestrator(AIOrchestrator):
    """
    Concrete implementation of AIOrchestrator.
    """
    async def execute_agents_concurrently(self, report_id: str, token_id: str) -> Dict[str, Any]:
        agent_results = await self.execute_agents(report_id, token_id)
        aggregated_data = self.aggregate_results(agent_results)

        # Determine overall status
        overall_status = "completed"
        if any(result["status"] == "failed" for result in agent_results.values()):
            overall_status = "partial_success"

        # Update in_memory_reports
        if report_id in in_memory_reports:
            in_memory_reports[report_id].update({
                "status": overall_status,
                "agent_results": aggregated_data["agent_results"]
            })
        else:
            logger.warning("Report ID %s not found in in_memory_reports during orchestration.", report_id)

        return aggregated_data

orchestrator = Orchestrator()
orchestrator.register_agent("dummy_agent", dummy_agent)