import asyncio
import logging
from backend.app.core.orchestrator import AIOrchestrator
from backend.app.services.agents.price_agent import run as price_agent_run
from backend.app.services.agents.trend_agent import run as trend_agent_run
from backend.app.services.agents.volume_agent import run as volume_agent_run
from backend.app.core.storage import save_report_data, set_report_status, try_set_processing
from backend.app.services.nlg.report_nlg_engine import ReportNLGEngine
from backend.app.services.summary.report_summary_engine import ReportSummaryEngine

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


    if not try_set_processing(report_id):
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

        # Generate NLG outputs
        nlg_engine = ReportNLGEngine()
        nlg_outputs = await nlg_engine.generate_nlg_outputs(combined_report_data)

        # Generate summary
        summary_engine = ReportSummaryEngine()
        scores = summary_engine.generate_scores(combined_report_data)
        final_narrative_summary = await summary_engine.build_final_summary(nlg_outputs, scores)

        # Determine overall status based on agent results
        overall_status = "completed"
        if any(result["status"] == "failed" for result in agent_results.values()):
            overall_status = "failed"
            logger.error(f"Report {report_id} completed with failures from one or more agents.")

        # Combine all into final_report
        final_report_content = {
            "section_texts": nlg_outputs,
            "final_summary": final_narrative_summary
        }

        # Save the combined_report_data first
        save_report_data(report_id, combined_report_data, update_status=False)
        # Then save the final report content
        save_report_data(report_id, final_report_content, key="final_report", update_status=False)

        set_report_status(report_id, overall_status)

        logger.info("Report %s %s.", report_id, overall_status)
        return True
    except asyncio.CancelledError:
        set_report_status(report_id, "cancelled")
        raise
    except Exception:
        logger.exception("Error processing report %s for token %s", report_id, token_id)
        set_report_status(report_id, "failed")
        raise