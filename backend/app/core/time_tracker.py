import datetime
from typing import Optional

from backend.app.cache.redis_client import redis_client

class TimeTracker:
    def __init__(self):
        self.redis = redis_client.client
        self.REPORT_PREFIX = "report_timer:"

    def start_timer(self, report_id: str):
        """
        Records the start timestamp for a given report_id in Redis.
        """
        if not self.redis:
            return
        key = f"{self.REPORT_PREFIX}{report_id}"
        redis_client.set_cache(key, datetime.datetime.now().isoformat())

    def finish_timer(self, report_id: str) -> Optional[float]:
        """
        Records the end timestamp for a given report_id, computes the total time taken,
        and removes the start timestamp from Redis.
        Returns the total time taken in seconds, or None if the start time was not found.
        """
        if not self.redis:
            return None
        key = f"{self.REPORT_PREFIX}{report_id}"
        start_time_str = redis_client.get_cache(key)
        
        if start_time_str:
            start_time = datetime.datetime.fromisoformat(start_time_str)
            end_time = datetime.datetime.now()
            total_time_seconds = (end_time - start_time).total_seconds()
            redis_client.delete_cache(key)  # Clean up the key after calculation
            return total_time_seconds
        return None

