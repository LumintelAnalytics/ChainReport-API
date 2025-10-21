import asyncio
import logging

logger = logging.getLogger(__name__)

# In a real application, this would be a more robust shared state management system (e.g., Redis, a database, or a dedicated in-memory store with proper locking).
# For now, a simple dictionary will simulate the state.
# NOTE: This in-memory lock is only suitable for single-process deployments.
# For multi-process or distributed deployments, consider using an external store
# like Redis or a database with appropriate distributed locking mechanisms.
report_status = {}
report_status_lock = asyncio.Lock()

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
    # Mark processing under lock
    async with report_status_lock:
        if report_id in report_status:
            raise ValueError(f"Report {report_id} is already being processed")
        report_status[report_id] = {"status": "processing", "token_id": token_id}

    logger.info("Processing report %s for token %s", report_id, token_id)

    try:
        await asyncio.sleep(5)  # Simulate work
        async with report_status_lock:
            if report_id in report_status and isinstance(report_status[report_id], dict):
                report_status[report_id]["status"] = "completed"
        logger.info("Report %s completed.", report_id)
        return True
    except asyncio.CancelledError:
        async with report_status_lock:
            if report_id in report_status:
                report_status[report_id]["status"] = "cancelled"
        raise
    except Exception:
        async with report_status_lock:
            if report_id in report_status:
                report_status[report_id]["status"] = "failed"
        logger.exception("Report %s failed.", report_id)
        raise

async def get_report_status(report_id: str):
    """
    Retrieves the status of a report.
    """
    async with report_status_lock:
        return report_status.get(report_id)