from pydantic import BaseModel
from typing import Optional

class ReportRequest(BaseModel):
    token_id: str
    parameters: Optional[dict] = None

class ReportResponse(BaseModel):
    report_id: str
    status: str
