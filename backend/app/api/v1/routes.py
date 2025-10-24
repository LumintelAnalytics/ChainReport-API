import logging
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.core.orchestrator import orchestrator, set_report_status, get_report_status as get_status
from backend.app.services.report_processor import process_report
from backend.app.services.report_service import generate_report, get_report_data

logger = logging.getLogger(__name__)

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

async def run_report_pipeline(report_id: str, token_id: str):
    # 1) Orchestrate agents and handle errors
    try:
        await orchestrator.execute_agents_concurrently(report_id, token_id)
    except Exception as e:
        logger.exception('Orchestrator failed for %s: %s', report_id, e)
        await set_report_status(report_id, {'status': 'failed', 'reason': str(e)})
        return

    # 2) Finalize processing if orchestrator didn't mark terminal error
    current = await get_status(report_id)
    if current and current.get('status') in ('failed', 'cancelled', 'partial_success'):
        logger.info('Report %s already in terminal state: %s', report_id, current.get('status'))
        return

    try:
        await process_report(report_id, token_id)
    except Exception as e:
        logger.exception('process_report failed for %s: %s', report_id, e)
        await set_report_status(report_id, {'status': 'failed', 'reason': str(e)})

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest, background_tasks: BackgroundTasks):
    report_response = await generate_report(request)
    report_id = report_response.report_id
    # Trigger the report processing as a background task
    background_tasks.add_task(run_report_pipeline, report_id, request.token_id)
    return report_response

@router.get("/reports/{report_id}/status")
async def get_report_status_endpoint(report_id: str):
    status_info = await get_status(report_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report_id": report_id, "status": status_info.get("status")}

@router.get("/reports/{report_id}/data")
async def get_report_data_endpoint(report_id: str):
    data = get_report_data(report_id)
    if data:
        return data

    status_info = await get_status(report_id)
    if status_info is None:
        raise HTTPException(status_code=404, detail="Report not found")

    status = status_info.get("status")
    if status == "processing":
        raise HTTPException(status_code=202, detail="Report is still processing")
    elif status in ["partial_success", "failed", "cancelled"]:
        raise HTTPException(status_code=422, detail=f"Report {status}, data not available")
    else:
        raise HTTPException(status_code=500, detail=f"Unexpected report status: {status}")
