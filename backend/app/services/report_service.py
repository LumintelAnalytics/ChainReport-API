from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.utils.id_generator import generate_report_id
from typing import Dict, Any
from backend.app.core.logger import services_logger
from backend.app.db.repositories.report_repository import ReportRepository
from backend.app.db.models.report_state import ReportStatusEnum

async def generate_report(request: ReportRequest, report_repository: ReportRepository) -> ReportResponse:
    services_logger.info(f"Generating new report for token_id: {request.token_id}")
    report_id = generate_report_id()
    await report_repository.create_report_entry(report_id)
    return ReportResponse(report_id=report_id, status=ReportStatusEnum.PENDING.value)

async def get_report_status(report_id: str, report_repository: ReportRepository) -> Dict[str, Any] | None:
    services_logger.info(f"Retrieving status for report_id: {report_id} from database.")
    report = await report_repository.get_report_state(report_id)
    if report:
        return {"report_id": report.report_id, "status": report.status.value}
    return None

async def get_report_data(report_id: str, report_repository: ReportRepository) -> Dict[str, Any] | None:
    services_logger.info(f"Attempting to retrieve data for report_id: {report_id}")
    report = await report_repository.get_report_state(report_id)
    if not report:
        services_logger.warning(f"Report with id {report_id} not found when attempting to retrieve data.")
        return None
    if report.status == ReportStatusEnum.COMPLETED:
        services_logger.info(f"Report {report_id} is completed, returning data.")
        return {
            "report_id": report.report_id,
            "data": report.final_report_json if report.final_report_json else report.partial_agent_output,
        }
    services_logger.info(f"Report {report_id} is in status: {report.status.value}, returning status only.")
    return {"report_id": report.report_id, "status": report.status.value, "detail": report.error_message}
