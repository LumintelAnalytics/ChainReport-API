import asyncio
from typing import Callable, Dict, Any
from urllib.parse import urlparse
from backend.app.services.report_service import in_memory_reports
from backend.app.core.logger import orchestrator_logger
from backend.app.services.agents.onchain_agent import fetch_onchain_metrics, fetch_tokenomics
from backend.app.core.config import settings

async def dummy_agent(report_id: str, token_id: str) -> Dict[str, Any]:
    """
    A dummy agent for testing purposes.
    """
    orchestrator_logger.info("Dummy agent received report_id: %s, token_id: %s", report_id, token_id)
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
        orchestrator_logger.info(f"Registering agent: {name}")
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
        return self._agents.copy()

    async def execute_agents(self, report_id: str, token_id: str) -> Dict[str, Any]:
        orchestrator_logger.info(f"Executing agents for report_id: {report_id}, token_id: {token_id}")
        tasks = {name: asyncio.create_task(agent_func(report_id, token_id)) for name, agent_func in self._agents.items()}
        results = {}

        for name, task in tasks.items():
            try:
                result = await asyncio.wait_for(task, timeout=10) # Added timeout
                results[name] = {"status": "completed", "data": result}
                orchestrator_logger.info(f"Agent {name} completed for report {report_id}.")
            except asyncio.TimeoutError: # Handle timeout specifically
                orchestrator_logger.exception("Agent %s timed out for report %s", name, report_id)
                results[name] = {"status": "failed", "error": "Agent timed out"}
            except Exception as e:
                orchestrator_logger.exception("Agent %s failed for report %s", name, report_id)
                results[name] = {"status": "failed", "error": str(e)}
        return results

    def aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator_logger.info("Aggregating results from executed agents.")
        """
        Aggregates the results from the executed AI agents.
        Args:
            results (dict): A dictionary of results from the executed agents.
        Returns:
            The aggregated result.
        """
        aggregated_data = {}
        for agent_name, agent_result in results.items():
            if agent_result["status"] == "completed" and "data" in agent_result:
                aggregated_data.update(agent_result["data"])
        return aggregated_data

class Orchestrator(AIOrchestrator):
    """
    Concrete implementation of AIOrchestrator.
    Instances of Orchestrator should be created using the `create_orchestrator` factory function.
    """
    async def execute_agents_concurrently(self, report_id: str, token_id: str) -> Dict[str, Any]:
        orchestrator_logger.info(f"Executing agents concurrently for report_id: {report_id}, token_id: {token_id}")
        agent_results = await self.execute_agents(report_id, token_id)
        aggregated_data = self.aggregate_results(agent_results)

        # Determine overall status
        overall_status = "completed"
        if any(result["status"] == "failed" for result in agent_results.values()):
            overall_status = "partial_success"
            orchestrator_logger.warning(f"Report {report_id} completed with partial success due to agent failures.")

        # Update in_memory_reports
        if report_id in in_memory_reports:
            in_memory_reports[report_id].update({
                "status": overall_status,
                "data": aggregated_data
            })
            orchestrator_logger.info(f"Report {report_id} status updated to {overall_status}.")
        else:
            orchestrator_logger.warning("Report ID %s not found in in_memory_reports during orchestration.", report_id)

        return aggregated_data

def create_orchestrator(register_dummy: bool = False) -> Orchestrator:
    """
    Factory function to create and configure an Orchestrator instance.

    Args:
        register_dummy (bool): If True, a 'dummy_agent' will be registered with the orchestrator.

    Returns:
        Orchestrator: A new instance of the Orchestrator.
    """
    def _is_valid_url(url: str | None, url_name: str) -> bool:
        if not url:
            orchestrator_logger.warning(f"Configuration Error: {url_name} is missing. Skipping agent registration.")
            return False
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc or parsed_url.scheme not in ("http", "https"):
            orchestrator_logger.warning(
                f"Configuration Error: {url_name} ('{url}') is not a valid HTTP/HTTPS URL. Skipping agent registration."
            )
            return False
        return True

    orch = Orchestrator()
    if register_dummy:
        orch.register_agent('dummy_agent', dummy_agent)

    # Configure and register onchain_metrics_agent
    onchain_metrics_url = settings.ONCHAIN_METRICS_URL
    if _is_valid_url(onchain_metrics_url, "ONCHAIN_METRICS_URL"):
        async def onchain_metrics_wrapper(report_id: str, token_id: str) -> Dict[str, Any]:
            params = {"token_id": token_id, "report_id": report_id}
            orchestrator_logger.info(f"Calling fetch_onchain_metrics for report_id: {report_id}, token_id: {token_id} with URL: {onchain_metrics_url}")
            return await fetch_onchain_metrics(url=onchain_metrics_url, params=params)
        orch.register_agent('onchain_metrics_agent', onchain_metrics_wrapper)
    else:
        orchestrator_logger.warning("Onchain metrics agent will not be registered due to invalid configuration.")

    # Configure and register tokenomics_agent
    tokenomics_url = settings.TOKENOMICS_URL
    if _is_valid_url(tokenomics_url, "TOKENOMICS_URL"):
        async def tokenomics_wrapper(report_id: str, token_id: str) -> Dict[str, Any]:
            params = {"token_id": token_id}
            orchestrator_logger.info(f"Calling fetch_tokenomics for report_id: {report_id}, token_id: {token_id} with URL: {tokenomics_url}")
            return await fetch_tokenomics(url=tokenomics_url, params=params)
        orch.register_agent('tokenomics_agent', tokenomics_wrapper)
    else:
        orchestrator_logger.warning("Tokenomics agent will not be registered due to invalid configuration.")

    return orch