import pytest
import time
from unittest.mock import MagicMock, patch
from backend.app.core.time_tracker import start_timer, finish_timer, REDIS_KEY_PREFIX

@pytest.fixture
def mock_redis_client():
    with patch('backend.app.core.time_tracker.redis_client') as mock:
        mock.get_cache.return_value = None  # Default: no cached value
        yield mock

def test_start_timer(mock_redis_client):
    report_id = "test_report_123"
    fixed_time = 1234567890.123456 # A fixed timestamp for consistent testing
    with patch('time.time', return_value=fixed_time):
        start_timer(report_id)

    key = f"{REDIS_KEY_PREFIX}{report_id}:start"
    mock_redis_client.set_cache.assert_called_once_with(key, str(fixed_time), ttl=3600)

def test_finish_timer_success(mock_redis_client):
    report_id = "test_report_456"
    start_fixed_time = time.time() - 10
    end_fixed_time = time.time()

    mock_redis_client.get_cache.return_value = str(start_fixed_time)  # Simulate start 10 seconds ago

    with patch('time.time', side_effect=[end_fixed_time]): # Mock time.time() only for the finish_timer call
        duration = finish_timer(report_id)

    start_key = f"{REDIS_KEY_PREFIX}{report_id}:start"
    duration_key = f"{REDIS_KEY_PREFIX}{report_id}:duration"

    mock_redis_client.get_cache.assert_called_once_with(start_key)
    mock_redis_client.set_cache.assert_called_with(duration_key, str(duration))
    mock_redis_client.delete_cache.assert_called_once_with(start_key)
    assert duration is not None
    assert duration == pytest.approx(10.0, rel=0.1)  # Allow for small time discrepancies

def test_finish_timer_no_start_time(mock_redis_client):
    report_id = "test_report_789"
    mock_redis_client.get_cache.return_value = None  # No start time in cache

    duration = finish_timer(report_id)

    start_key = f"{REDIS_KEY_PREFIX}{report_id}:start"

    mock_redis_client.get_cache.assert_called_once_with(start_key)
    mock_redis_client.set_cache.assert_not_called()
    mock_redis_client.delete_cache.assert_not_called()
    assert duration is None

