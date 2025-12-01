import asyncio
import logging
from backend.app.core.orchestrator import Orchestrator
from backend.app.services.agents.price_agent import run as price_agent_run
from backend.app.services.agents.trend_agent import run as trend_agent_run
from backend.app.services.agents.volume_agent import run as volume_agent_run
from backend.app.core.storage import try_set_processing
from backend.app.services.nlg.report_nlg_engine import ReportNLGEngine
from backend.app.services.summary.report_summary_engine import ReportSummaryEngine
from backend.app.db.repositories.report_repository import ReportRepository
from backend.app.db.models.report_state import ReportStatusEnum # Import ReportStatusEnum

logger = logging.getLogger(__name__)



async def process_report(report_id: str, token_id: str, report_repository: ReportRepository) -> bool:
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
        orchestrator = Orchestrator(report_repository.session)
        orchestrator.register_agent("price_agent", price_agent_run)
        orchestrator.register_agent("trend_agent", trend_agent_run)
        orchestrator.register_agent("volume_agent", volume_agent_run)

        agent_results = await orchestrator.execute_agents(report_id, token_id)
        combined_report_data = orchestrator.aggregate_results(agent_results)

        # Generate NLG outputs
        await report_repository.update_report_status(report_id, ReportStatusEnum.GENERATING_NLG)
        nlg_engine = ReportNLGEngine()
        try:
            nlg_outputs = await nlg_engine.generate_nlg_outputs(combined_report_data)
            await report_repository.update_report_status(report_id, ReportStatusEnum.NLG_COMPLETED)
        except Exception as e:
            logger.exception("Error generating NLG outputs for report %s", report_id)
            await report_repository.update_partial(report_id, {"status": ReportStatusEnum.FAILED, "error": str(e)})
            raise

        # Generate summary
        await report_repository.update_report_status(report_id, ReportStatusEnum.GENERATING_SUMMARY)
        summary_engine = ReportSummaryEngine()
        try:
            scores_input = {
                "tokenomics_data": combined_report_data.get("tokenomics", {}),
                "sentiment_data": combined_report_data.get("social_sentiment", {}),
                "code_audit_data": combined_report_data.get("code_audit", {}),
                "team_data": combined_report_data.get("team_documentation", {})
            }
            scores = summary_engine.generate_scores(scores_input)

            agent_errors = {}
            for agent_name, result in agent_results.items():
                if result.get("status") == ReportStatusEnum.FAILED.value and result.get("error"):
                    agent_errors[agent_name] = {
                        "timestamp": result.get("timestamp"), # Assuming timestamp is part of the agent result
                        "error_message": result.get("error")
                    }

            final_narrative_summary = summary_engine.build_final_summary(nlg_outputs, scores, agent_errors)
            await report_repository.update_report_status(report_id, ReportStatusEnum.SUMMARY_COMPLETED)
        except Exception as e:
            logger.exception("Error generating summary for report %s", report_id)
            await report_repository.update_partial(report_id, {"status": ReportStatusEnum.FAILED, "error": str(e)})
            raise

        # Determine overall status based on agent results
        overall_status = ReportStatusEnum.COMPLETED
        if any(result.get("status") == ReportStatusEnum.FAILED.value for result in agent_results.values()):
            overall_status = ReportStatusEnum.FAILED
            logger.error("Report %s completed with failures from one or more agents.", report_id)

        # Combine all into final_report
        final_report_content = {
            "section_texts": nlg_outputs,
            "final_summary": final_narrative_summary
        }

        # Save the combined_report_data first
        await report_repository.store_partial_report_results(report_id, combined_report_data)
        # Then save the final report content
        await report_repository.save_final_report(report_id, final_report_content)

        await report_repository.update_report_status(report_id, overall_status)

        logger.info("Report %s %s.", report_id, overall_status.value)
        return True
    except asyncio.CancelledError:
        await report_repository.update_report_status(report_id, ReportStatusEnum.FAILED)
        raise
    except Exception:
        logger.exception("Error processing report %s for token %s", report_id, token_id)
        await report_repository.update_report_status(report_id, ReportStatusEnum.FAILED)
        raise