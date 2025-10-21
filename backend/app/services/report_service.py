import logging
from backend.app.models.report_models import ReportRequest, ReportResponse
from backend.app.utils.id_generator import generate_report_id
from typing import Dict

logger = logging.getLogger(__name__)

# In-memory storage for reports (to be replaced with persistent storage)
in_memory_reports: Dict[str, Dict] = {}

async def generate_report(request: ReportRequest) -> ReportResponse:
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
        in_memory_reports[report_id].update(data)
    else:
        # Handle case where report_id does not exist, or log a warning
        logger.warning("Report ID %s not found for saving data.", report_id)
