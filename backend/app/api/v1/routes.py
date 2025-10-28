import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.services.report_service import generate_report, in_memory_reports, get_report_status_from_memory, get_report_data
from backend.app.core.orchestrator import create_orchestrator
import asyncio


logger = logging.getLogger(__name__)

router = APIRouter()

# Dummy Agent for demonstration
async def dummy_agent_one(report_id: str, token_id: str) -> dict:
    print(f"Dummy Agent One running for report {report_id} and token {token_id}")
    await asyncio.sleep(2) # Simulate async work
    return {"agent_one_data": "data_from_agent_one"}

async def dummy_agent_two(report_id: str, token_id: str) -> dict:
    print(f"Dummy Agent Two running for report {report_id} and token {token_id}")
    await asyncio.sleep(1.5) # Simulate async work
    return {"agent_two_data": "data_from_agent_two"}

# Register agents
orchestrator_instance = create_orchestrator()
orchestrator_instance.register_agent("AgentOne", dummy_agent_one)
orchestrator_instance.register_agent("AgentTwo", dummy_agent_two)

@router.get("/")
async def read_root():
    return {"message": "Welcome to API v1"}

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest, background_tasks: BackgroundTasks):
    report_response = await generate_report(request)
    report_id = report_response.report_id
    # Execute agents concurrently in a background task
    background_tasks.add_task(orchestrator_instance.execute_agents_concurrently, report_id, request.token_id)
    return report_response

@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str):
    report = get_report_status_from_memory(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report_id": report_id, "status": report["status"]}

@router.get("/reports/{report_id}/data")
async def get_report_data_endpoint(report_id: str):
    report_result = get_report_data(report_id)
    if report_result:
        if "data" in report_result:
            return report_result
        elif report_result.get("status") == "processing":
            # Match test expectations exactly
            return JSONResponse(
                status_code=202,
                content={
                    "detail": "Report is still processing.",
                },
            )
        elif report_result.get("status") == "failed":
            return JSONResponse(
                status_code=409,
                content={
                    "report_id": report_id,
                    "message": "Report failed",
                    "detail": report_result.get("detail", "Report processing failed."),
                },
            )
    raise HTTPException(status_code=404, detail="Report not found or not completed")
