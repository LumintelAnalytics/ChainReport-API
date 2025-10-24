import asyncio
import logging
from typing import Callable, Dict, Any, List
from backend.app.services.report_service import in_memory_reports

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """
    Base class for coordinating multiple AI agents.
    Designed to handle parallel asynchronous agent calls.
    """

    def __init__(self):
        self.agents: Dict[str, Callable] = {}

    def register_agent(self, name: str, agent_func: Callable):
        """
        Registers an AI agent with the orchestrator.
        Args:
            name (str): The name of the agent.
            agent_func (Callable): The asynchronous function representing the agent.
        """
        self.agents[name] = agent_func

    async def execute_agents(self, report_id: str, token_id: str) -> Dict[str, Any]:
        tasks = {name: asyncio.create_task(agent_func(report_id, token_id)) for name, agent_func in self.agents.items()}
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

        # Update in_memory_reports using the new adapter
        await set_report_status(report_id, {
            "status": overall_status,
            "agent_results": aggregated_data["agent_results"]
        })

        return aggregated_data

orchestrator = Orchestrator()

async def set_report_status(report_id: str, status_info: Dict[str, Any]) -> bool:
    """
    Sets the status of a report in in_memory_reports, preventing overwrites of terminal statuses.
    """
    if report_id not in in_memory_reports:
        logger.warning("Report ID %s not found in in_memory_reports.", report_id)
        return False

    current_status = in_memory_reports[report_id].get("status")
    if current_status in ("failed", "cancelled", "partial_success"):
        logger.info("Not overwriting terminal status for %s: %s", report_id, current_status)
        return False

    in_memory_reports[report_id].update(status_info)
    return True

async def get_report_status(report_id: str) -> Dict[str, Any] | None:
    """
    Retrieves the status of a report from in_memory_reports.
    """
    return in_memory_reports.get(report_id)