from fastapi import APIRouter
from app.models.report_models import ReportRequest, ReportResponse
from app.services.report_service import generate_report

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Welcome to API v1"}

@router.post("/report/generate", response_model=ReportResponse)
async def generate_report_endpoint(request: ReportRequest):
    return await generate_report(request)
