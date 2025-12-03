import logging
from datetime import datetime
from backend.app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "report_timer:"

def start_timer(report_id: str):
    """
    Records the start timestamp for a given report_id in Redis.
    """
    try:
        start_time = datetime.now().isoformat()
        key = f"{REDIS_KEY_PREFIX}{report_id}"
        redis_client.set_cache(key, start_time, ttl=3600 * 24)  # Store for 24 hours
        logger.info(f"Timer started for report_id: {report_id} at {start_time}")
    except Exception as e:
        logger.error(f"Failed to start timer for report_id {report_id}: {e}", exc_info=True)

def finish_timer(report_id: str) -> float | None:
    """
    Retrieves the start timestamp, calculates the duration, and removes the timer from Redis.
    Returns the duration in seconds or None if the timer was not found or an error occurred.
    """
    key = f"{REDIS_KEY_PREFIX}{report_id}"
    try:
        start_time_str = redis_client.get_cache(key)
        if start_time_str:
            redis_client.delete_cache(key)
            start_time = datetime.fromisoformat(start_time_str.decode('utf-8'))
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Timer finished for report_id: {report_id}. Duration: {duration:.2f} seconds.")
            return duration
        else:
            logger.warning(f"Timer not found for report_id: {report_id}")
            return None
    except Exception as e:
        logger.error(f"Failed to finish timer for report_id {report_id}: {e}", exc_info=True)
        return None
