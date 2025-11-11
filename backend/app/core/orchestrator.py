import asyncio
from typing import Callable, Dict, Any
from urllib.parse import urlparse
from backend.app.services.report_service import in_memory_reports
from backend.app.core.logger import orchestrator_logger
from backend.app.services.agents.onchain_agent import fetch_onchain_metrics, fetch_tokenomics
from backend.app.services.agents.social_sentiment_agent import SocialSentimentAgent
from backend.app.services.agents.team_doc_agent import TeamDocAgent
from backend.app.services.agents.code_audit_agent import CodeAuditAgent # Import CodeAuditAgent
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
                result = await asyncio.wait_for(task, timeout=settings.AGENT_TIMEOUT) # Added timeout
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
            overall_status = "failed"
            orchestrator_logger.error(f"Report {report_id} failed due to one or more agent failures.")
        elif any(result["status"] == "partial_success" for result in agent_results.values()):
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

    # Configure and register Onchain Data Agent
    onchain_metrics_url = settings.ONCHAIN_METRICS_URL
    tokenomics_url = settings.TOKENOMICS_URL

    if _is_valid_url(onchain_metrics_url, "ONCHAIN_METRICS_URL") and _is_valid_url(tokenomics_url, "TOKENOMICS_URL"):
        async def onchain_data_agent(report_id: str, token_id: str) -> Dict[str, Any]:
            orchestrator_logger.info(f"Calling Onchain Data Agent for report_id: {report_id}, token_id: {token_id}")
            onchain_metrics_params = {"token_id": token_id, "report_id": report_id}
            tokenomics_params = {"token_id": token_id}

            onchain_metrics_task = asyncio.create_task(fetch_onchain_metrics(url=onchain_metrics_url, params=onchain_metrics_params, token_id=token_id))
            tokenomics_task = asyncio.create_task(fetch_tokenomics(url=tokenomics_url, params=tokenomics_params, token_id=token_id))

            onchain_metrics_result = {}
            tokenomics_result = {}

            onchain_metrics_result, tokenomics_result = await asyncio.gather(
                asyncio.wait_for(onchain_metrics_task, timeout=settings.AGENT_TIMEOUT - 1),
                asyncio.wait_for(tokenomics_task, timeout=settings.AGENT_TIMEOUT - 1),
                return_exceptions=True  # This will allow us to handle exceptions for each task individually
            )

            # Handle individual task results and exceptions
            if isinstance(onchain_metrics_result, asyncio.TimeoutError):
                orchestrator_logger.error("Onchain metrics fetch timed out for report %s", report_id)
                onchain_metrics_result = {"error": "Onchain metrics fetch timed out"}
            elif isinstance(onchain_metrics_result, Exception):
                orchestrator_logger.error("Onchain metrics fetch failed for report %s", report_id)
                onchain_metrics_result = {"error": str(onchain_metrics_result)}

            if isinstance(tokenomics_result, asyncio.TimeoutError):
                orchestrator_logger.error("Tokenomics fetch timed out for report %s", report_id)
                tokenomics_result = {"error": "Tokenomics fetch timed out"}
            elif isinstance(tokenomics_result, Exception):
                orchestrator_logger.error("Tokenomics fetch failed for report %s", report_id)
                tokenomics_result = {"error": str(tokenomics_result)}

            return {
                "onchain_metrics": onchain_metrics_result,
                "tokenomics": tokenomics_result
            }
        orch.register_agent('onchain_data_agent', onchain_data_agent)
    else:
        orchestrator_logger.warning("Onchain Data Agent will not be registered due to invalid configuration.")

    # Configure and register Social Sentiment Agent
    async def social_sentiment_agent_func(report_id: str, token_id: str) -> Dict[str, Any]:
        orchestrator_logger.info(f"Calling Social Sentiment Agent for report_id: {report_id}, token_id: {token_id}")
        agent = SocialSentimentAgent()
        social_sentiment_data = {}
        try:
            social_data = await asyncio.wait_for(agent.fetch_social_data(token_id), timeout=settings.AGENT_TIMEOUT - 1)
            sentiment_report = await asyncio.wait_for(agent.analyze_sentiment(social_data), timeout=settings.AGENT_TIMEOUT - 1)
            social_sentiment_data = {
                "social_sentiment": {
                    "overall_sentiment": sentiment_report.get("overall_sentiment"),
                    "score": sentiment_report.get("score"),
                    "summary": sentiment_report.get("details") # Storing details as summary for now
                }
            }
            orchestrator_logger.info(f"Social Sentiment Agent completed for report {report_id}.")
        except asyncio.TimeoutError:
            orchestrator_logger.error("Social Sentiment Agent timed out for report %s", report_id)
            social_sentiment_data = {"social_sentiment": {"error": "Agent timed out"}}
        except Exception as e:
            orchestrator_logger.exception("Social Sentiment Agent failed for report %s", report_id)
            social_sentiment_data = {"social_sentiment": {"error": str(e)}}
        return social_sentiment_data
    orch.register_agent('social_sentiment_agent', social_sentiment_agent_func)

    # Configure and register Team and Documentation Agent
    async def team_documentation_agent(report_id: str, token_id: str) -> Dict[str, Any]:
        orchestrator_logger.info(f"Calling Team and Documentation Agent for report_id: {report_id}, token_id: {token_id}")
        agent = TeamDocAgent()
        team_analysis = []
        whitepaper_summary = {}
        
        # Placeholder for fetching token-related data (URLs, whitepaper text)
        # In a real scenario, this data would be fetched based on token_id
        # For now, we'll use dummy data or assume it comes from settings
        team_profile_urls = settings.TEAM_PROFILE_URLS.get(token_id, [])
        whitepaper_text_source = settings.WHITEPAPER_TEXT_SOURCES.get(token_id, "")

        try:
            # Scrape team profiles
            orchestrator_logger.info(f"Scraping team profiles for token {token_id} from URLs: {team_profile_urls}")
            team_analysis = await asyncio.wait_for(
                asyncio.to_thread(agent.scrape_team_profiles, team_profile_urls),
                timeout=settings.AGENT_TIMEOUT - 1
            )
            orchestrator_logger.info(f"Team profile scraping completed for token {token_id}.")

            # Analyze whitepaper
            if whitepaper_text_source:
                orchestrator_logger.info(f"Analyzing whitepaper for token {token_id} from source: {whitepaper_text_source}")
                whitepaper_summary = await asyncio.wait_for(
                    asyncio.to_thread(agent.analyze_whitepaper, whitepaper_text_source),
                    timeout=settings.AGENT_TIMEOUT - 1
                )
                orchestrator_logger.info(f"Whitepaper analysis completed for token {token_id}.")
            else:
                orchestrator_logger.warning(f"No whitepaper text source provided for token {token_id}. Skipping whitepaper analysis.")

        except asyncio.TimeoutError:
            orchestrator_logger.error("Team and Documentation Agent timed out for report %s", report_id)
            return {"team_documentation": {"error": "Agent timed out"}}
        except Exception as e:
            orchestrator_logger.exception("Team and Documentation Agent failed for report %s", report_id)
            return {"team_documentation": {"error": str(e)}}
        
        return {
            "team_documentation": {
                "team_analysis": team_analysis,
                "whitepaper_summary": whitepaper_summary
            }
        }
    orch.register_agent('team_documentation_agent', team_documentation_agent)

    # Configure and register Code/Audit Agent
    code_audit_repo_url = settings.CODE_AUDIT_REPO_URL
    if _is_valid_url(code_audit_repo_url, "CODE_AUDIT_REPO_URL"):
        async def code_audit_agent_func(report_id: str, token_id: str) -> Dict[str, Any]:
            orchestrator_logger.info(f"Calling Code/Audit Agent for report_id: {report_id}, token_id: {token_id}")
            code_metrics_data = {}
            audit_summary_data = []
            try:
                async with CodeAuditAgent() as agent:
                    # Fetch repo metrics
                    orchestrator_logger.info(f"Fetching repository metrics for {code_audit_repo_url}")
                    code_metrics = await asyncio.wait_for(
                        agent.fetch_repo_metrics(code_audit_repo_url),
                        timeout=settings.AGENT_TIMEOUT - 1
                    )
                    code_metrics_data = code_metrics.model_dump()

                    # Analyze code activity
                    orchestrator_logger.info(f"Analyzing code activity for {code_audit_repo_url}")
                    code_activity_analysis = await asyncio.wait_for(
                        agent.analyze_code_activity(code_metrics),
                        timeout=settings.AGENT_TIMEOUT - 1
                    )
                    code_metrics_data.update({"activity_analysis": code_activity_analysis})

                    # Search and summarize audit reports
                    orchestrator_logger.info(f"Searching and summarizing audit reports for {code_audit_repo_url}")
                    audit_summary = await asyncio.wait_for(
                        agent.search_and_summarize_audit_reports(code_audit_repo_url),
                        timeout=settings.AGENT_TIMEOUT - 1
                    )
                    audit_summary_data = audit_summary

            except asyncio.TimeoutError:
                orchestrator_logger.error("Code/Audit Agent timed out for report %s", report_id)
                return {"code_audit": {"error": "Agent timed out", "code_metrics": code_metrics_data, "audit_summary": audit_summary_data}}
            except Exception as e:
                orchestrator_logger.exception("Code/Audit Agent failed for report %s", report_id)
                return {"code_audit": {"error": str(e), "code_metrics": code_metrics_data, "audit_summary": audit_summary_data}}
            
            return {
                "code_audit": {
                    "code_metrics": code_metrics_data,
                    "audit_summary": audit_summary_data
                }
            }
        orch.register_agent('code_audit_agent', code_audit_agent_func)
    else:
        orchestrator_logger.warning("Code/Audit Agent will not be registered due to invalid CODE_AUDIT_REPO_URL configuration.")


    return orch