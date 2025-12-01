import time
import pytest
import datetime
from backend.app.core.time_tracker import TimeTracker
from backend.app.cache.redis_client import redis_client

@pytest.fixture(scope="module")
def time_tracker():
    # Ensure Redis is clean before and after tests
    if redis_client.client:
        redis_client.client.flushdb()
    tracker = TimeTracker()
    yield tracker
    if redis_client.client:
        redis_client.client.flushdb()

def test_start_and_finish_timer(time_tracker):
    report_id = "test_report_1"
    time_tracker.start_timer(report_id)
    time.sleep(0.1)  # Simulate some work
    total_time = time_tracker.finish_timer(report_id)

    if time_tracker.redis:
        assert total_time is not None
        assert total_time >= 0.1
    else:
        assert total_time is None

def test_finish_timer_no_start(time_tracker):
    report_id = "test_report_no_start"
    total_time = time_tracker.finish_timer(report_id)
    assert total_time is None

def test_timer_persistence(time_tracker):
    report_id = "test_report_persistence"
    time_tracker.start_timer(report_id)

    # Simulate a new instance of TimeTracker (e.g., in a different request)
    new_tracker = TimeTracker()

    if new_tracker.redis:
        # Directly get from redis to check persistence
        key = f"{new_tracker.REPORT_PREFIX}{report_id}"
        start_time_str = redis_client.get_cache(key)
        assert start_time_str is not None
    
        start_time = datetime.datetime.fromisoformat(start_time_str)
        assert start_time is not None
    
        total_time = new_tracker.finish_timer(report_id)
        assert total_time is not None
        assert redis_client.get_cache(key) is None # Ensure key is deleted after finishing
    else:
        total_time = new_tracker.finish_timer(report_id)
        assert total_time is None
