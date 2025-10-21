from fastapi import APIRouter
from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.services.report_service import generate_report
from backend.app.core.orchestrator import orchestrator
import asyncio

router = APIRouter()

# Dummy Agent for demonstration
async def dummy_agent_one(report_id: str, token_id: str) -> dict:
    print(f"Dummy Agent One running for report {report_id} and token {token_id}")
    await asyncio.sleep(1) # Simulate async work
    return {"agent_one_data": "data_from_agent_one"}

async def dummy_agent_two(report_id: str, token_id: str) -> dict:
    print(f"Dummy Agent Two running for report {report_id} and token {token_id}")
    await asyncio.sleep(0.5) # Simulate async work
    return {"agent_two_data": "data_from_agent_two"}

# Register agents
orchestrator.register_agent("AgentOne", dummy_agent_one)
orchestrator.register_agent("AgentTwo", dummy_agent_two)

@router.get("/")
async def read_root():
    return {"message": "Welcome to API v1"}

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest):
    report_response = await generate_report(request)
    report_id = report_response.report_id
    # Execute agents concurrently
    await orchestrator.execute_agents_concurrently(report_id, request.token_id)
    return report_response
