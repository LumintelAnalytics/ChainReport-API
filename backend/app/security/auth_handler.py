
import jwt
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.core.config import settings

security = HTTPBearer()

def signJWT(user_id: str) -> Dict[str, str]:
    payload = {
        "user_id": user_id,
        "expires": str(datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return {
        "access_token": token
    }

def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return decoded_token if datetime.strptime(decoded_token["expires"], "%Y-%m-%d %H:%M:%S.%f") >= datetime.utcnow() else None
    except:
        return {}

def auth_wrapper(auth: HTTPAuthorizationCredentials = Security(security)):
    return decodeJWT(auth.credentials)
