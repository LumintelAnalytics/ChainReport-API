from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.api.v1.routes import router as v1_router
from backend.app.core.exceptions import ReportNotFoundException, AgentExecutionException
from backend.app.core.logger import api_logger

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

@app.exception_handler(ReportNotFoundException)
async def report_not_found_exception_handler(request: Request, exc: ReportNotFoundException):
    api_logger.error(f"ReportNotFoundException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": "Report not found",
            "detail": exc.detail
        },
    )

@app.exception_handler(AgentExecutionException)
async def agent_execution_exception_handler(request: Request, exc: AgentExecutionException):
    api_logger.error(f"AgentExecutionException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": "Agent execution failed",
            "detail": exc.detail
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    api_logger.error(f"HTTPException: {exc.detail} (Status Code: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "detail": exc.detail
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    api_logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "detail": "An unexpected error occurred."
        }
    )

app.include_router(v1_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
