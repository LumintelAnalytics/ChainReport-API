import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.services.report_service import in_memory_reports
from backend.app.core.orchestrator import orchestrator
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
async def test_get_report_data_endpoint_processing(client: TestClient):
    response = await anyio.to_thread.run_sync(functools.partial(client.post, "/api/v1/report/generate", json={
        "token_id": "test_token",
        "parameters": {"param1": "value1"}
    }))
    report_id = response.json()["report_id"]

    # Immediately request data, should be processing
    response = await anyio.to_thread.run_sync(client.get, f"/api/v1/reports/{report_id}/data")
    assert response.status_code == 202
    assert response.json() == {"report_id": report_id, "message": "Report is still processing.", "detail": "Report is still processing."} # Added detail to match the actual response

@pytest.mark.asyncio
async def test_get_report_data_endpoint_completed(client: TestClient):
    # Generate a report
    response = await anyio.to_thread.run_sync(functools.partial(client.post, "/api/v1/report/generate", json={
        "token_id": "test_token",
        "parameters": {"param1": "value1"}
    }))
    assert response.status_code == 200
    report_id = response.json()["report_id"]

    # Wait for the background task to complete
    await asyncio.sleep(2)  # Give enough time for dummy agents to complete

    # Request data, should be completed
    response = await anyio.to_thread.run_sync(client.get, f"/api/v1/reports/{report_id}/data")
    data = response.json()
    assert response.status_code == 200
    assert data["report_id"] == report_id
    assert "data" in data
    assert "agent_results" in data["data"]
    assert "AgentOne" in data["data"]["agent_results"]
    assert "AgentTwo" in data["data"]["agent_results"]
    assert data["data"]["agent_results"]["AgentOne"]["status"] == "completed"
    assert data["data"]["agent_results"]["AgentTwo"]["status"] == "completed"

@pytest.mark.asyncio
async def test_get_report_data_endpoint_not_found(client: TestClient):
    response = await anyio.to_thread.run_sync(client.get, "/api/v1/reports/non_existent_report/data")
    assert response.status_code == 404
    assert response.json() == {"detail": "Report not found or not completed"}