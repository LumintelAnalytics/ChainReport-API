import logging
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.cache.redis_client import redis_client
from backend.app.db.repositories.report_repository import ReportRepository
from backend.app.db.models.report_state import ReportState

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "report_timer:"

def start_timer(report_id: str):
    """
    Records the start timestamp for a given report_id in Redis.
    """
    try:
        start_time = datetime.now(timezone.utc).isoformat()
        key = f"{REDIS_KEY_PREFIX}{report_id}"
        redis_client.set_cache(key, start_time, ttl=3600 * 24)  # Store for 24 hours
        logger.info(f"Timer started for report_id: {report_id} at {start_time}")
    except Exception as e:
        logger.error(f"Failed to start timer for report_id {report_id}: {e}", exc_info=True)

async def finish_timer(report_id: str, db: AsyncSession) -> float | None:
    """
    Retrieves the start timestamp, calculates the duration, and removes the timer from Redis.
    Returns the duration in seconds or None if the timer was not found or an error occurred.
    Also, logs a warning and stores it in report state if processing exceeds five minutes.
    """
    key = f"{REDIS_KEY_PREFIX}{report_id}"
    report_repo = ReportRepository(lambda: db) # type: ignore
    try:
        start_time_str = redis_client.get_cache(key)
        if start_time_str:
            redis_client.delete_cache(key)
            start_time = datetime.fromisoformat(start_time_str.decode('utf-8')).replace(tzinfo=timezone.utc)
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Timer finished for report_id: {report_id}. Duration: {duration:.2f} seconds.")

            if duration > 300:  # 5 minutes
                warning_message = {
                    "timestamp": end_time.isoformat(),
                    "message": f"Report processing time exceeded 5 minutes. Duration: {duration:.2f} seconds.",
                    "threshold": "5 minutes"
                }
                logger.warning(
                    f"Report {report_id} processing time exceeded 5 minutes. Duration: {duration:.2f} seconds."
                )

                report_state: ReportState | None = await report_repo.get_report_by_id(report_id)
                if report_state:
                    timing_alerts = report_state.timing_alerts if report_state.timing_alerts else []
                    timing_alerts.append(warning_message)
                    await report_repo.update_timing_alerts(report_id, timing_alerts)
                else:
                    logger.error(f"ReportState not found for report_id {report_id}. Cannot store timing alert.")

            return duration
        else:
            logger.warning(f"Timer not found for report_id: {report_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to finish timer for report_id {report_id}: {e}", exc_info=True)
        return None
