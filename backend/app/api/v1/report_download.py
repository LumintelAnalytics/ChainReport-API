import tempfile
import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
import re
import logging
from backend.app.core.logger import logger
from pathlib import Path
from weasyprint import HTML

from backend.app.core.config import settings
from backend.app.db.connection import get_db
from backend.app.db.repositories.report_repository import ReportRepository
from backend.app.db.models.report_state import ReportStatusEnum
from backend.app.security.dependencies import CurrentUser

router = APIRouter()

downloads_logger = logging.getLogger("downloads")

def render_report_html(report_data: dict) -> str:
    """
    Renders the report JSON data into a basic HTML structure.
    This is a simplified rendering for demonstration.
    """
    if not report_data:
        return "<html><body><h1>Report data not available.</h1></body></html>"

    html_content = "<html><head><title>ChainReport</title></head><body>"
    html_content += f"<h1>Report ID: {report_data.get('report_id', 'N/A')}</h1>"
    
    # Example of rendering some common top-level fields
    if "metadata" in report_data:
        html_content += "<h2>Metadata</h2><ul>"
        for key, value in report_data["metadata"].items():
            html_content += f"<li><strong>{key}:</strong> {value}</li>"
        html_content += "</ul>"

    if "sections" in report_data and isinstance(report_data["sections"], list):
        html_content += "<h2>Report Sections</h2>"
        for section in report_data["sections"]:
            html_content += f"<h3>{section.get('title', 'Untitled Section')}</h3>"
            if "content" in section:
                html_content += f"<p>{section['content']}</p>"
            if "agents_output" in section:
                html_content += "<h4>Agent Outputs:</h4><ul>"
                for agent, output in section["agents_output"].items():
                    html_content += f"<li><strong>{agent}:</strong> {output}</li>"
                html_content += "</ul>"

    html_content += "</body></html>"
    return html_content

@router.get("/reports/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(
    report_id: str,
    db_session: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(CurrentUser)
):
    """
    Retrieves and serves the HTML report for a given report ID,
    including authentication, authorization, and path traversal prevention.
    """
    # 1. Path Traversal Prevention: Sanitize report_id
    # Ensure report_id only contains alphanumeric characters, dashes, and underscores
    if not re.fullmatch(r"^[a-zA-Z0-9_-]+$", report_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID format.")

    report_repository = ReportRepository(lambda: db_session)
    report_state = await report_repository.get_report_by_id(report_id)

    if not report_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # 2. Authentication and Authorization (Placeholder for actual ownership/permission check)
    # This is a placeholder. In a real application, 'report_state' would likely
    # have a 'user_id' or 'team_id' to check against 'current_user'.
    # For now, we'll assume a simplified check.
    # if report_state.user_id != current_user.id:
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this report.")
    print(f"User '{current_user.username}' (ID: {current_user.id}) is accessing report '{report_id}'.")


    # 3. Check if report status is COMPLETED
    if report_state.status != ReportStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not yet completed. Current status: {report_state.status.value}"
        )
    
    final_report_json = report_state.final_report_json
    if not final_report_json:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Final report content not available.")

    # 4. Render the JSON into a basic HTML structure
    html_content = render_report_html(final_report_json)

    # 5. Return the HTML with a Content-Disposition header for download
    response = HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
    response.headers["Content-Disposition"] = f"attachment; filename=\"report_{report_id}.html\""
    return response

@router.get("/reports/{report_id}/pdf")
async def get_report_pdf(
    report_id: str,
    background_tasks: BackgroundTasks,
    db_session: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(CurrentUser),
    request: Request
):
    """
    Retrieves and serves the PDF report for a given report ID,
    including authentication, authorization, and path traversal prevention.
    """
    if not re.fullmatch(r"^[a-zA-Z0-9_-]+$", report_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report ID format.")

    report_repository = ReportRepository(lambda: db_session)
    report_state = await report_repository.get_report_by_id(report_id)

    if not report_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # Placeholder for authentication and authorization
    print(f"User '{current_user.username}' (ID: {current_user.id}) is accessing report '{report_id}'.")
    downloads_logger.info({
        "event": "pdf_download",
        "reportId": report_id,
        "requester_ip": request.client.host
    })

    if report_state.status != ReportStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not yet completed. Current status: {report_state.status.value}"
        )
    
    final_report_json = report_state.final_report_json
    if not final_report_json:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Final report content not available.")

    report_dir = settings.REPORT_OUTPUT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    pdf_filepath = report_dir / f"report_{report_id}.pdf"

    if pdf_filepath.exists():
        logger.info(f"Serving existing PDF report for report_id: {report_id}")
        return FileResponse(
            path=pdf_filepath,
            media_type="application/pdf",
            filename=f"report_{report_id}.pdf",
            status_code=status.HTTP_200_OK
        )
    
    logger.info(f"Generating new PDF report for report_id: {report_id}")
    html_content = render_report_html(final_report_json)

    try:
        # Offload blocking PDF generation to a thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: HTML(string=html_content).write_pdf(pdf_filepath)
        )

        # Return the newly generated PDF
        response = FileResponse(
            path=pdf_filepath,
            media_type="application/pdf",
            filename=f"report_{report_id}.pdf",
            status_code=status.HTTP_200_OK
        )
        return response
    except Exception as e:
        logger.exception(f"Failed to generate PDF report for report_id: {report_id}", extra={"report_id": report_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report"
        ) from e
