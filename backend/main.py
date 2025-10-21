from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.routes import router as v1_router

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(v1_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
