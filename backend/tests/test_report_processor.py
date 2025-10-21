import pytest
import asyncio
from backend.app.services.report_processor import process_report, report_status, report_status_lock, get_report_status

@pytest.fixture(autouse=True)
async def clear_report_status():
    async with report_status_lock:
        report_status.clear()
    yield
    async with report_status_lock:
        report_status.clear()

@pytest.mark.asyncio
async def test_process_report_success():
    report_id = "test_report_1"
    token_id = "test_token_1"
    
    result = await process_report(report_id, token_id)
    assert result is True
    
    async with report_status_lock:
        assert report_status[report_id]["status"] == "completed"
        assert report_status[report_id]["token_id"] == token_id

@pytest.mark.asyncio
async def test_process_report_already_processing():
    report_id = "test_report_2"
    token_id = "test_token_2"

    # Start processing but don't await it to simulate concurrency
    task = asyncio.create_task(process_report(report_id, token_id))
    await asyncio.sleep(0.1)  # Give it a moment to set status to 'processing'

    with pytest.raises(ValueError, match=f"Report {report_id} is already being processed"):
        await process_report(report_id, token_id)
    
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task # Await the cancelled task to ensure it raises CancelledError

@pytest.mark.asyncio
async def test_process_report_cancellation():
    report_id = "test_report_3"
    token_id = "test_token_3"

    task = asyncio.create_task(process_report(report_id, token_id))
    await asyncio.sleep(0.1)  # Let it start processing

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    async with report_status_lock:
        assert report_status[report_id]["status"] == "cancelled"

@pytest.mark.asyncio
async def test_process_report_exception_handling():
    report_id = "test_report_4"
    token_id = "test_token_4"

    # Temporarily modify process_report to raise an exception
    original_sleep = asyncio.sleep
    async def mock_sleep_raise(*args, **kwargs):
        raise Exception("Simulated processing error")
    asyncio.sleep = mock_sleep_raise

    with pytest.raises(Exception, match="Simulated processing error"):
        await process_report(report_id, token_id)

    async with report_status_lock:
        assert report_status[report_id]["status"] == "failed"
    
    asyncio.sleep = original_sleep # Restore original sleep

@pytest.mark.asyncio
async def test_get_report_status():
    report_id = "test_report_5"
    token_id = "test_token_5"

    async with report_status_lock:
        report_status[report_id] = {"status": "initial", "token_id": token_id}
    
    status = await get_report_status(report_id)
    assert status == {"status": "initial", "token_id": token_id}

    status = await get_report_status("non_existent_report")
    assert status is None

@pytest.mark.asyncio
async def test_concurrent_different_reports():
    report_id_1 = "concurrent_report_1"
    token_id_1 = "concurrent_token_1"
    report_id_2 = "concurrent_report_2"
    token_id_2 = "concurrent_token_2"

    task1 = asyncio.create_task(process_report(report_id_1, token_id_1))
    task2 = asyncio.create_task(process_report(report_id_2, token_id_2))

    await asyncio.gather(task1, task2)

    async with report_status_lock:
        assert report_status[report_id_1]["status"] == "completed"
        assert report_status[report_id_2]["status"] == "completed"
        assert report_status[report_id_1]["token_id"] == token_id_1
        assert report_status[report_id_2]["token_id"] == token_id_2
