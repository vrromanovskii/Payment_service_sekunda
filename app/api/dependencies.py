# импорт инструментов FastAPI
from fastapi import Header, HTTPException, Depends
# импортируем settings для получения API_KEY из переменных окружения
from app.core.config import settings

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY: # проверяем совпадение ключа
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key # если ключ совпал, возвращаем его занчение