import pytest
from unittest.mock import Mock, patch
from backend.app.core.time_tracker import start_timer, finish_timer
from datetime import datetime, timedelta

@pytest.fixture
def mock_redis_client():
    with patch('backend.app.core.time_tracker.redis_client', autospec=True) as mock_client:
        mock_client.set_cache = Mock()
        mock_client.get_cache = Mock()
        mock_client.delete_cache = Mock()
        yield mock_client

@pytest.mark.asyncio
async def test_start_and_finish_timer(mock_redis_client):
    report_id = "test_report_123"

    # Mock the return value for get to simulate a delay
    start_time_iso = (datetime.now() - timedelta(seconds=5)).isoformat()
    mock_redis_client.get_cache.return_value = start_time_iso

    await start_timer(report_id)
    mock_redis_client.set_cache.assert_called_once()

    duration = await finish_timer(report_id)

            mock_redis_client.get_cache.assert_called_with(f"report:{report_id}:start_time")
            assert mock_redis_client.set_cache.call_count == 3  # start_time, end_time, duration
            mock_redis_client.delete_cache.assert_called_with(f"report:{report_id}:start_time")    assert isinstance(duration, float)
    assert duration > 0

@pytest.mark.asyncio
async def test_finish_timer_no_start_time(mock_redis_client):
    report_id = "test_report_456"
    mock_redis_client.get_cache.return_value = None  # Simulate no start time found

    duration = await finish_timer(report_id)
    
    assert duration is None
    mock_redis_client.set_cache.assert_not_called()
    mock_redis_client.delete_cache.assert_not_called()
