# app/api/dependencies.py
from fastapi import Header, HTTPException, Depends
from app.core.config import settings

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key