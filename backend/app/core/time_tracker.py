import datetime
import json
from typing import Optional

from backend.app.cache.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

async def start_timer(report_id: str):
    """
    Records the start timestamp for a given report_id in Redis.
    """
    start_time = datetime.datetime.now(datetime.timezone.utc)
    await redis_client.set(f"report:{report_id}:start_time", start_time.isoformat())
    logger.info(f"Timer started for report_id {report_id} at {start_time}")

async def finish_timer(report_id: str) -> Optional[float]:
    """
    Records the end timestamp, computes the total time taken, and stores it in Redis.
    Returns the total time in seconds if successful, else None.
    """
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time_str = await redis_client.get(f"report:{report_id}:start_time")

    if start_time_str:
        start_time = datetime.datetime.fromisoformat(start_time_str)
        duration = (end_time - start_time).total_seconds()
        await redis_client.set(f"report:{report_id}:end_time", end_time.isoformat())
        await redis_client.set(f"report:{report_id}:duration", str(duration))
        logger.info(f"Timer finished for report_id {report_id} at {end_time}. Duration: {duration:.2f} seconds.")
        return duration
    else:
        logger.warning(f"Start time not found for report_id {report_id}. Cannot finish timer.")
        return None

async def get_total_time(report_id: str) -> Optional[float]:
    """
    Retrieves the total time taken for a report from Redis.
    Returns the total time in seconds if available, else None.
    """
    duration_str = await redis_client.get(f"report:{report_id}:duration")
    if duration_str:
        return float(duration_str)
    return None
