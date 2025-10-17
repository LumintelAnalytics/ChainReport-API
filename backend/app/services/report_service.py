from app.models.report_models import ReportRequest, ReportResponse
from app.utils.id_generator import generate_report_id
from typing import Dict

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
