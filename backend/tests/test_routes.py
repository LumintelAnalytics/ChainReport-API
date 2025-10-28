import pytest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.services.report_service import in_memory_reports
from backend.app.core.orchestrator import orchestrator
from backend.app.services import report_processor
from backend.app.services.report_processor import report_status, report_status_lock, get_report_status

import pytest_asyncio
import anyio

@pytest_asyncio.fixture(autouse=True)
def clear_in_memory_reports():
    in_memory_reports.clear()
    yield
    in_memory_reports.clear()

@pytest_asyncio.fixture(autouse=True)
async def clear_report_processor_status():
    async with report_status_lock:
        report_status.clear()
    yield
    async with report_status_lock:
        report_status.clear()

@pytest_asyncio.fixture
async def client():
    with TestClient(app) as tc:
        yield tc

@pytest.mark.asyncio
async def test_get_report_data_endpoint_processing(client: TestClient):
    # Temporarily mock asyncio.sleep in dummy agents to prevent them from completing
    original_dummy_agent_one = orchestrator.agents["AgentOne"]
    original_dummy_agent_two = orchestrator.agents["AgentTwo"]

    async def mock_sleep_agent(*args, **kwargs):
        await asyncio.sleep(100) # Simulate a very long running task

    orchestrator.register_agent("AgentOne", mock_sleep_agent)
    orchestrator.register_agent("AgentTwo", mock_sleep_agent)

    try:
        # Generate a report to get a report_id
        response = client.post("/api/v1/report/generate", json={
            "token_id": "test_token",
            "parameters": {"param1": "value1"}
        })
        assert response.status_code == 200
        report_id = response.json()["report_id"]

        response = client.get(f"/api/v1/reports/{report_id}/status")
        assert response.status_code == 200
        assert response.json() == {"report_id": report_id, "status": "partial_success"}
    finally:
        # Restore original dummy agents
        orchestrator.register_agent("AgentOne", original_dummy_agent_one)
        orchestrator.register_agent("AgentTwo", original_dummy_agent_two)

@pytest.mark.asyncio
async def test_get_report_data_endpoint_completed(client: TestClient):
    # Generate a report
    response = client.post("/api/v1/report/generate", json={
        "token_id": "test_token",
        "parameters": {"param1": "value1"}
    })
    assert response.status_code == 200
    report_id = response.json()["report_id"]

    # Wait for the background task to complete
    await asyncio.sleep(6)  # Give enough time for dummy agents to complete

    response = client.get(f"/api/v1/reports/{report_id}/data")
    data = response.json()
    assert response.status_code == 200
    assert data["report_id"] == report_id
    assert "data" in data
    assert "AgentOne" in data["data"]
    assert "AgentTwo" in data["data"]
    assert data["data"]["AgentOne"]["status"] == "completed"
    assert data["data"]["AgentTwo"]["status"] == "completed"

@pytest.mark.asyncio
async def test_get_report_data_endpoint_not_found(client: TestClient):
    response = client.get("/api/v1/reports/non_existent_report/data")
    assert response.status_code == 404
    assert response.json() == {"detail": "Report not found or not completed"}