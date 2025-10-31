import asyncio
import logging
from backend.app.core.orchestrator import AIOrchestrator
from backend.app.services.agents.price_agent import run as price_agent_run
from backend.app.services.agents.trend_agent import run as trend_agent_run
from backend.app.services.agents.volume_agent import run as volume_agent_run
from backend.app.core.storage import save_report_data, set_report_status, get_report_status

logger = logging.getLogger(__name__)



async def process_report(report_id: str, token_id: str) -> bool:
    """
    Simulates a background report generation process.
    Updates report_status to 'processing' and then to 'completed' on success.

    Raises:
        ValueError: If report_id is already being processed.
        Exception: Any underlying exceptions are re-raised after marking status.
    Returns:
        True on success.
    """


    if not storage.try_set_processing(report_id):
        logger.info("Report %s is already being processed, skipping.", report_id)
        raise ValueError(f"Report {report_id} is already being processed")

    logger.info("Processing report %s for token %s", report_id, token_id)
    try:
        orchestrator = AIOrchestrator()
        orchestrator.register_agent("price_agent", price_agent_run)
        orchestrator.register_agent("trend_agent", trend_agent_run)
        orchestrator.register_agent("volume_agent", volume_agent_run)

        agent_results = await orchestrator.execute_agents(report_id, token_id)
        combined_report_data = orchestrator.aggregate_results(agent_results)

        save_report_data(report_id, combined_report_data)
        set_report_status(report_id, "completed")

        logger.info("Report %s completed.", report_id)
        return True
    except asyncio.CancelledError:
        set_report_status(report_id, "cancelled")
        raise
    except Exception:
        logger.exception("Error processing report %s for token %s", report_id, token_id)
        storage.set_report_status(report_id, "failed")
        raise