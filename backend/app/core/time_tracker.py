import time
import logging
from backend.app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "report_timer:"

def start_timer(report_id: str):
    """
    Starts a timer for a given report_id by storing the current timestamp in Redis.
    """
    try:
        start_timestamp = time.time()
        key = f"{REDIS_KEY_PREFIX}{report_id}:start"
        redis_client.set_cache(key, str(start_timestamp), ttl=3600)
        logger.info(f"Timer started for report_id {report_id} at {start_timestamp}")
    except Exception as e:
        logger.error(f"Error starting timer for report_id {report_id}: {e}")

def finish_timer(report_id: str) -> float | None:
    """
    Finishes the timer for a given report_id, calculates the duration, and stores it.
    Returns the total time taken in seconds, or None if an error occurred.
    """
    try:
        end_timestamp = time.time()
        start_key = f"{REDIS_KEY_PREFIX}{report_id}:start"
        start_timestamp_str = redis_client.get_cache(start_key)

        if start_timestamp_str is None:
            logger.warning(f"No start timer found for report_id {report_id}. Cannot finish timer.")
            return None

        start_timestamp = float(start_timestamp_str)
        duration = end_timestamp - start_timestamp

        # Store the duration
        duration_key = f"{REDIS_KEY_PREFIX}{report_id}:duration"
        redis_client.set_cache(duration_key, str(duration))
        
        # Clean up the start key
        redis_client.delete_cache(start_key)

        logger.info(f"Timer finished for report_id {report_id}. Duration: {duration:.2f} seconds.")
        return duration
    except Exception as e:
        logger.error(f"Error finishing timer for report_id {report_id}: {e}")
        return None
