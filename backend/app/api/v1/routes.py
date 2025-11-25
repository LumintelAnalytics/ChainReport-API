from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.connection import get_session
from backend.app.db.repositories.report_repository import ReportRepository
from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.services.report_service import generate_report, get_report_status, get_report_data
from backend.app.services.report_processor import process_report
from backend.app.core.logger import api_logger
from backend.app.core.exceptions import ReportNotFoundException
from backend.app.db.models.report_state import ReportStatusEnum

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Welcome to API v1"}

from backend.app.db.connection import get_session # Added for background task

async def _run_agents_in_background(report_id: str, token_id: str):
    async for session in get_session():
        report_repository = ReportRepository(session)
        try:
            await report_repository.update_report_status(report_id, ReportStatusEnum.RUNNING_AGENTS)
        await process_report(report_id, token_id, report_repository)
        await report_repository.update_report_status(report_id, ReportStatusEnum.COMPLETED)
    except Exception as e:
        api_logger.error(f"Report processing failed for report {report_id}: {e}")
        await report_repository.update_partial(report_id, {"status": ReportStatusEnum.FAILED, "error": str(e)})

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
    api_logger.info(f"Received report generation request for token_id: {request.token_id}")
    report_repository = ReportRepository(session)
    report_response = await generate_report(request, report_repository)
    report_id = report_response.report_id
    background_tasks.add_task(_run_agents_in_background, report_id, request.token_id)
    return report_response

@router.get("/reports/{report_id}/status")
async def get_report_status_endpoint(report_id: str, session: AsyncSession = Depends(get_session)):
    api_logger.info(f"Received status request for report_id: {report_id}")
    report_repository = ReportRepository(session)
    report = await get_report_status(report_id, report_repository)
    if not report:
        api_logger.error(f"Report with id {report_id} not found for status request.")
        raise ReportNotFoundException(detail="Report not found")
    return {"report_id": report_id, "status": report["status"]}

@router.get("/reports/{report_id}/data")
async def get_report_data_endpoint(report_id: str, session: AsyncSession = Depends(get_session)):
    api_logger.info(f"Received data request for report_id: {report_id}")
    report_repository = ReportRepository(session)
    report_result = await get_report_data(report_id, report_repository)
    if report_result:
        if report_result.get("status") == ReportStatusEnum.COMPLETED.value:
            api_logger.info(f"Returning data for report_id: {report_id}")
            return report_result
        elif report_result.get("status") == ReportStatusEnum.RUNNING_AGENTS.value or report_result.get("status") == ReportStatusEnum.PENDING.value or report_result.get("status") == ReportStatusEnum.RUNNING_AGENTS.value or report_result.get("status") == ReportStatusEnum.GENERATING_NLG.value or report_result.get("status") == ReportStatusEnum.GENERATING_SUMMARY.value:
            api_logger.warning(f"Report {report_id} is still processing.")
            return JSONResponse(
                status_code=202,
                content={
                    "detail": "Report is still processing.",
                },
            )
        elif report_result.get("status") == ReportStatusEnum.FAILED.value:
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
