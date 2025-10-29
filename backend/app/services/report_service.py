from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.utils.id_generator import generate_report_id
from typing import Dict
from backend.app.core.logger import services_logger

# In-memory storage for reports (to be replaced with persistent storage)
in_memory_reports: Dict[str, Dict] = {}

async def generate_report(request: ReportRequest) -> ReportResponse:
    services_logger.info(f"Generating new report for token_id: {request.token_id}")
    report_id = generate_report_id()
    # Store a placeholder report object
    in_memory_reports[report_id] = {
        "token_id": request.token_id,
        "parameters": request.parameters,
        "status": "processing",
        "report_id": report_id
    }
    return ReportResponse(report_id=report_id, status="processing")

async def save_report_data(report_id: str, data: Dict):
    if report_id in in_memory_reports:
        services_logger.info(f"Saving data for report_id: {report_id}")
        in_memory_reports[report_id].update(data)
    else:
        # Handle case where report_id does not exist, or log a warning
        services_logger.warning("Report ID %s not found for saving data.", report_id)

def get_report_status_from_memory(report_id: str) -> Dict | None:
    services_logger.info(f"Retrieving status for report_id: {report_id} from memory.")
    return in_memory_reports.get(report_id)

def get_report_data(report_id: str) -> Dict | None:
    services_logger.info(f"Attempting to retrieve data for report_id: {report_id}")
    report = in_memory_reports.get(report_id)
    if not report:
        services_logger.warning(f"Report with id {report_id} not found when attempting to retrieve data.")
        return None
    if report.get("status") == "completed":
        services_logger.info(f"Report {report_id} is completed, returning data.")
        return {
            "report_id": report_id,
            "data": {"agent_results": report.get("agent_results", {})},
        }
    services_logger.info(f"Report {report_id} is in status: {report.get("status")}, returning status only.")
    return {"report_id": report_id, "status": report.get("status")}
