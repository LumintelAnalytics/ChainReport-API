from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import HTTPException
import os

from backend.app.core.config import settings

router = APIRouter()

@router.get("/reports/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(report_id: str):
    """
    Serves the HTML report for a given report ID.
    """
    file_name = f"report_{report_id}.html"
    file_path = os.path.join(settings.REPORT_OUTPUT_DIR, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report HTML not found")
    
    return FileResponse(file_path, media_type="text/html")
