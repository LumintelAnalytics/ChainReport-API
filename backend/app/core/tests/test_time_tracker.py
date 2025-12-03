import datetime
import pytest
from unittest.mock import AsyncMock, patch

from backend.app.core.time_tracker import start_timer, finish_timer, get_total_time

@pytest.fixture
def mock_redis_client():
    with patch('backend.app.core.time_tracker.redis_client', new_callable=AsyncMock) as mock_client:
        yield mock_client

@pytest.mark.asyncio
async def test_start_timer(mock_redis_client):
    report_id = "test_report_123"
    await start_timer(report_id)

    mock_redis_client.set.assert_called_once()
    args, _ = mock_redis_client.set.call_args
    assert args[0] == f"report:{report_id}:start_time"
    start_time_str = args[1]
    datetime.datetime.fromisoformat(start_time_str) # Should not raise an error

@pytest.mark.asyncio
async def test_finish_timer_success(mock_redis_client):
    report_id = "test_report_456"
    mock_start_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)
    mock_redis_client.get.return_value = mock_start_time.isoformat()

    duration = await finish_timer(report_id)

    assert mock_redis_client.get.call_count == 1
    assert mock_redis_client.get.call_args[0][0] == f"report:{report_id}:start_time"

    assert mock_redis_client.set.call_count == 2 # for end_time and duration
    set_calls = mock_redis_client.set.call_args_list

    # Check end_time set call
    assert set_calls[0][0][0] == f"report:{report_id}:end_time"
    datetime.datetime.fromisoformat(set_calls[0][0][1]) # Should not raise an error

    # Check duration set call
    assert set_calls[1][0][0] == f"report:{report_id}:duration"
    assert isinstance(float(set_calls[1][0][1]), float)
    assert float(set_calls[1][0][1]) > 0 # Duration should be positive

    assert isinstance(duration, float)
    assert duration > 0

@pytest.mark.asyncio
async def test_finish_timer_no_start_time(mock_redis_client):
    report_id = "test_report_789"
    mock_redis_client.get.return_value = None

    duration = await finish_timer(report_id)

    mock_redis_client.get.assert_called_once_with(f"report:{report_id}:start_time")
    mock_redis_client.set.assert_not_called()
    assert duration is None

@pytest.mark.asyncio
async def test_get_total_time(mock_redis_client):
    report_id = "test_report_010"
    mock_duration = 123.45
    mock_redis_client.get.return_value = str(mock_duration)

    total_time = await get_total_time(report_id)

    mock_redis_client.get.assert_called_once_with(f"report:{report_id}:duration")
    assert total_time == mock_duration

@pytest.mark.asyncio
async def test_get_total_time_no_duration(mock_redis_client):
    report_id = "test_report_111"
    mock_redis_client.get.return_value = None

    total_time = await get_total_time(report_id)

    mock_redis_client.get.assert_called_once_with(f"report:{report_id}:duration")
    assert total_time is None
