import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from backend.app.core.time_tracker import start_timer, finish_timer
from backend.app.db.models.report_state import ReportState
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.repositories.report_repository import ReportRepository # Import for type hinting

@pytest.fixture
def mock_redis_client():
    # Patch redis_client where it's used in time_tracker.py
    with patch('backend.app.core.time_tracker.redis_client', new_callable=Mock) as mock:
        yield mock

@pytest.fixture
def mock_report_repository_instance():
    # This mocks the instance that would be created inside finish_timer
    return AsyncMock(spec=ReportRepository)

@pytest.fixture
def mock_report_repository_class(mock_report_repository_instance):
    with patch('backend.app.core.time_tracker.ReportRepository') as mock_class:
        mock_class.return_value = mock_report_repository_instance
        yield mock_class

@pytest.fixture
def mock_async_session():
    return AsyncMock(spec=AsyncSession)


def test_start_timer(mock_redis_client):
    report_id = "test_report_1"
    start_timer(report_id)
    mock_redis_client.set_cache.assert_called_once()
    args, kwargs = mock_redis_client.set_cache.call_args
    assert args[0] == f"report_timer:{report_id}"
    assert "ttl" in kwargs

@pytest.mark.asyncio
async def test_finish_timer_under_five_minutes(mock_redis_client, mock_report_repository_class, mock_report_repository_instance, mock_async_session):
    report_id = "test_report_2"
    
    # Simulate start_timer
    mock_redis_client.get_cache.return_value = datetime.now().isoformat().encode('utf-8')
    
    duration = await finish_timer(report_id, mock_async_session)
    
    mock_redis_client.get_cache.assert_called_once_with(f"report_timer:{report_id}")
    mock_redis_client.delete_cache.assert_called_once_with(f"report_timer:{report_id}")
    assert isinstance(duration, float)
    mock_report_repository_instance.get_report_by_id.assert_not_called()
    mock_report_repository_instance.update_timing_alerts.assert_not_called()

@pytest.mark.asyncio
async def test_finish_timer_over_five_minutes(mock_redis_client, mock_report_repository_class, mock_report_repository_instance, mock_async_session):
    report_id = "test_report_3"
    
    # Simulate start_timer more than 5 minutes ago
    five_minutes_ago = datetime.now() - timedelta(minutes=5, seconds=1)
    mock_redis_client.get_cache.return_value = five_minutes_ago.isoformat().encode('utf-8')
    
    mock_report_state = ReportState(report_id=report_id)
    mock_report_repository_instance.get_report_by_id.return_value = mock_report_state
    mock_report_repository_instance.update_timing_alerts.return_value = mock_report_state # Ensure a return value
    
    duration = await finish_timer(report_id, mock_async_session)
    
    mock_redis_client.get_cache.assert_called_once_with(f"report_timer:{report_id}")
    mock_redis_client.delete_cache.assert_called_once_with(f"report_timer:{report_id}")
    assert isinstance(duration, float)
    assert duration > 300
    
    mock_report_repository_instance.get_report_by_id.assert_called_once_with(report_id)
    mock_report_repository_instance.update_timing_alerts.assert_called_once()
    
    args, _ = mock_report_repository_instance.update_timing_alerts.call_args
    assert args[0] == report_id
    updated_alerts = args[1]
    assert isinstance(updated_alerts, list)
    assert len(updated_alerts) == 1
    assert "Report processing time exceeded 5 minutes" in updated_alerts[0]["message"]
    assert "timestamp" in updated_alerts[0]
    assert "threshold" in updated_alerts[0]

@pytest.mark.asyncio
async def test_finish_timer_not_found(mock_redis_client, mock_report_repository_class, mock_report_repository_instance, mock_async_session):
    report_id = "test_report_4"
    mock_redis_client.get_cache.return_value = None
    
    duration = await finish_timer(report_id, mock_async_session)
    
    mock_redis_client.get_cache.assert_called_once_with(f"report_timer:{report_id}")
    mock_redis_client.delete_cache.assert_not_called()
    assert duration is None
    mock_report_repository_instance.get_report_by_id.assert_not_called()
    mock_report_repository_instance.update_timing_alerts.assert_not_called()

@pytest.mark.asyncio
async def test_finish_timer_exception(mock_redis_client, mock_report_repository_class, mock_report_repository_instance, mock_async_session):
    report_id = "test_report_5"
    mock_redis_client.get_cache.side_effect = Exception("Redis error")
    
    duration = await finish_timer(report_id, mock_async_session)
    
    assert duration is None
    mock_report_repository_instance.get_report_by_id.assert_not_called()
    mock_report_repository_instance.update_timing_alerts.assert_not_called()
