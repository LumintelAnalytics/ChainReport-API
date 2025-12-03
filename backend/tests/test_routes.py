import pytest
from fastapi.testclient import TestClient
from backend.main import app
import pytest_asyncio
import anyio
import functools

@pytest_asyncio.fixture(autouse=True)
def clear_in_memory_reports():
    in_memory_reports.clear()
    yield
    in_memory_reports.clear()

@pytest_asyncio.fixture
async def client():
    with TestClient(app) as tc:
        yield tc

@pytest.mark.asyncio
async def test_get_report_data_endpoint_processing(client: TestClient, mocker):
    # Mock the background task to prevent it from completing during the test
    mocker.patch("backend.app.core.orchestrator.Orchestrator.execute_agents_concurrently", new_callable=mocker.AsyncMock)

    response = await anyio.to_thread.run_sync(
        functools.partial(
            client.post,
            "/api/v1/report/generate",
            json={"token_id": "test_token", "parameters": {"param1": "value1"}},
        )
    )
    assert response.status_code == 200
    report_id = response.json()["report_id"]

    # No need for anyio.sleep here, as the background task is mocked to not complete

    # Immediately request data, should be processing
    response = await anyio.to_thread.run_sync(client.get, f"/api/v1/reports/{report_id}/data")
    assert response.status_code == 202
    assert response.json() == {"detail": "Report is still processing."}

@pytest.mark.asyncio
async def test_get_report_data_endpoint_completed(client: TestClient):
    # Generate a report
    response = await anyio.to_thread.run_sync(
        functools.partial(
            client.post,
            "/api/v1/report/generate",
            json={"token_id": "test_token", "parameters": {"param1": "value1"}},
        )
    )
    assert response.status_code == 200
    report_id = response.json()["report_id"]

    # Wait for the background task to complete with a polling loop
    for _ in range(10):
        status_response = await anyio.to_thread.run_sync(client.get, f"/api/v1/reports/{report_id}/status")
        if status_response.status_code == 200 and status_response.json().get("status") == "completed":
            break
        await anyio.sleep(0.5)
    else:
        pytest.fail("Report did not complete in time")

    # Request data, should be completed
    response = await anyio.to_thread.run_sync(client.get, f"/api/v1/reports/{report_id}/data")
    data = response.json()
    assert response.status_code == 200
    assert data["report_id"] == report_id
    assert "data" in data
    assert "agent_one_data" in data["data"]
    assert "agent_two_data" in data["data"]
    assert data["data"]["agent_one_data"] == "data_from_agent_one"
    assert data["data"]["agent_two_data"] == "data_from_agent_two"

@pytest.mark.asyncio
async def test_get_report_data_endpoint_not_found(client: TestClient):
    response = await anyio.to_thread.run_sync(client.get, "/api/v1/reports/non_existent_report/data")
    assert response.status_code == 404
    assert response.json() == {"message": "Report not found", "detail": "Report not found or not completed"}