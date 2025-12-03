import asyncio
import time
from datetime import datetime
from backend.app.cache.redis_client import redis_client

async def start_timer(report_id: str):
    """
    Records the start timestamp for a given report_id in Redis.
    """
    start_time = datetime.now().isoformat()
    await asyncio.to_thread(redis_client.set_cache, f"report:{report_id}:start_time", start_time)
    print(f"Timer started for report_id: {report_id} at {start_time}")

async def finish_timer(report_id: str):
    """
    Records the end timestamp for a given report_id, computes the total time taken,
    and stores it in Redis.
    """
    end_time = datetime.now().isoformat()
    start_time_str = await asyncio.to_thread(redis_client.get_cache, f"report:{report_id}:start_time")

    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str)
        duration = (datetime.fromisoformat(end_time) - start_time).total_seconds()
        await asyncio.to_thread(redis_client.set_cache, f"report:{report_id}:end_time", end_time)
        await asyncio.to_thread(redis_client.set_cache, f"report:{report_id}:duration", str(duration))
        print(f"Timer finished for report_id: {report_id} at {end_time}. Duration: {duration:.2f} seconds.")
        # Optionally, remove the start_time from Redis after calculation if no longer needed
        await asyncio.to_thread(redis_client.delete_cache, f"report:{report_id}:start_time")
        return duration
    else:
        print(f"No start time found for report_id: {report_id}. Cannot compute duration.")
        return None

