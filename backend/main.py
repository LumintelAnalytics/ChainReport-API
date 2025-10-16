from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
