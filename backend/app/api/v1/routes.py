from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.services.report_service import generate_report, in_memory_reports, get_report_status_from_memory, get_report_data
from backend.app.core.orchestrator import create_orchestrator
from backend.app.core.logger import api_logger
from backend.app.core.exceptions import ReportNotFoundException
import asyncio

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

async def _run_agents_in_background(report_id: str, token_id: str):
    try:
        await orchestrator_instance.execute_agents_concurrently(report_id, token_id)
    except Exception as e:
        api_logger.error(f"Agent execution failed for report {report_id}: {e}")
        # Here you might want to update the report status to 'failed' in in_memory_reports
        # For now, we'll just log it.
        if report_id in in_memory_reports:
            in_memory_reports[report_id]["status"] = "failed"
            in_memory_reports[report_id]["detail"] = f"Agent execution failed: {e}"

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest, background_tasks: BackgroundTasks):
    api_logger.info(f"Received report generation request for token_id: {request.token_id}")
    report_response = await generate_report(request)
    report_id = report_response.report_id
    background_tasks.add_task(_run_agents_in_background, report_id, request.token_id)
    return report_response

@router.get("/reports/{report_id}/status")
async def get_report_status(report_id: str):
    api_logger.info(f"Received status request for report_id: {report_id}")
    report = get_report_status_from_memory(report_id)
    if not report:
        api_logger.error(f"Report with id {report_id} not found for status request.")
        raise ReportNotFoundException(detail="Report not found")
    return {"report_id": report_id, "status": report["status"]}

@router.get("/reports/{report_id}/data")
async def get_report_data_endpoint(report_id: str):
    api_logger.info(f"Received data request for report_id: {report_id}")
    report_result = get_report_data(report_id)
    if report_result:
        if "data" in report_result:
            api_logger.info(f"Returning data for report_id: {report_id}")
            return report_result
        elif report_result.get("status") == "processing":
            api_logger.warning(f"Report {report_id} is still processing.")
            # Match test expectations exactly
            return JSONResponse(
                status_code=202,
                content={
                    "detail": "Report is still processing.",
                },
            )
        elif report_result.get("status") == "failed":
            api_logger.error(f"Report {report_id} failed with detail: {report_result.get("detail", "N/A")}")
            return JSONResponse(
                status_code=409,
                content={
                    "report_id": report_id,
                    "message": "Report failed",
                    "detail": report_result.get("detail", "Report processing failed."),
                },
            )
    api_logger.error(f"Report with id {report_id} not found or not completed for data request.")
    raise ReportNotFoundException(detail="Report not found or not completed")
