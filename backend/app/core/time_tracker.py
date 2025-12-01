import time
from datetime import datetime
from backend.app.cache.redis_client import redis_client

REPORT_TIMER_PREFIX = "report_timer:"

def start_timer(report_id: str):
    """
    Records the start timestamp for a given report_id in Redis.
    """
    key = f"{REPORT_TIMER_PREFIX}{report_id}:start"
    timestamp = datetime.now().isoformat()
    redis_client.set(key, timestamp)

def finish_timer(report_id: str) -> float:
    """
    Records the end timestamp for a given report_id in Redis and
    computes the total time taken.
    Returns the total time in seconds.
    """
    end_key = f"{REPORT_TIMER_PREFIX}{report_id}:end"
    start_key = f"{REPORT_TIMER_PREFIX}{report_id}:start"

    end_timestamp = datetime.now()
    redis_client.set(end_key, end_timestamp.isoformat())

    start_timestamp_str = redis_client.get(start_key)
    if start_timestamp_str:
        start_timestamp = datetime.fromisoformat(start_timestamp_str.decode())
        total_time = (end_timestamp - start_timestamp).total_seconds()
        return total_time
    return 0.0

