from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from backend.app.core.config import settings
from backend.app.api.v1.routes import router as v1_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
