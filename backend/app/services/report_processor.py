import logging
from backend.app.core.orchestrator import set_report_status, get_report_status

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
    # Mark processing
    current_status = await get_report_status(report_id)
    if current_status and current_status.get("status") in ("processing", "completed", "failed", "cancelled", "partial_success"):
        raise ValueError(f"Report {report_id} is already in a terminal or processing state")
    await set_report_status(report_id, {"status": "processing", "token_id": token_id})

    logger.info("Processing report %s for token %s", report_id, token_id)

    try:
        await asyncio.sleep(5)  # Simulate work
        await set_report_status(report_id, {"status": "completed"})
        logger.info("Report %s completed.", report_id)
        return True
    except asyncio.CancelledError:
        await set_report_status(report_id, {"status": "cancelled"})
        raise
    except Exception:
        await set_report_status(report_id, {"status": "failed"})
        logger.exception("Report %s failed.", report_id)
        raise