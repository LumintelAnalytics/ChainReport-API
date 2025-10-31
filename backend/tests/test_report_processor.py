import pytest
import asyncio
from backend.app.services.report_processor import process_report
from backend.app.core.storage import get_report_status, set_report_status, REPORT_STORE

@pytest.fixture(autouse=True)
async def clear_report_status():
    REPORT_STORE.clear()
    yield
    REPORT_STORE.clear()

@pytest.mark.asyncio
async def test_process_report_success():
    report_id = "test_report_1"
    token_id = "test_token_1"
    
    result = await process_report(report_id, token_id)
    assert result is True
    
    status_data = get_report_status(report_id)
    assert status_data == "completed"
    # Further checks can be added here to validate the content of the report data
    # For example: assert REPORT_STORE[report_id]["data"] is not None


@pytest.mark.asyncio
async def test_process_report_already_processing():
    report_id = "test_report_2"
    token_id = "test_token_2"

    set_report_status(report_id, "processing")

    with pytest.raises(ValueError, match=f"Report {report_id} is already being processed"):
        await process_report(report_id, token_id)

@pytest.mark.asyncio
async def test_process_report_cancellation():
    report_id = "test_report_3"
    token_id = "test_token_3"

    task = asyncio.create_task(process_report(report_id, token_id))
    await asyncio.sleep(0.1)  # Let it start processing

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    status = get_report_status(report_id)
    assert status == "cancelled"

@pytest.mark.asyncio
async def test_process_report_exception_handling(mocker):
    report_id = "test_report_4"
    token_id = "test_token_4"

    mocker.patch("backend.app.core.orchestrator.AIOrchestrator.execute_agents", side_effect=Exception("Simulated orchestration error"))

    with pytest.raises(Exception, match="Simulated orchestration error"):
        await process_report(report_id, token_id)

    status = get_report_status(report_id)
    assert status == "failed"

@pytest.mark.asyncio
async def test_get_report_status():
    report_id = "test_report_5"
    token_id = "test_token_5"

    set_report_status(report_id, "initial")
    
    status = get_report_status(report_id)
    assert status == "initial"

    status = get_report_status("non_existent_report")
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

    status1 = get_report_status(report_id_1)
    status2 = get_report_status(report_id_2)
    assert status1 == "completed"
    assert status2 == "completed"
