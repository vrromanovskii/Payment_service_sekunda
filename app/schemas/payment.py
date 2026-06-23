# app/schemas/payment.py
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

# Схема для создания платежа (запрос)
class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма платежа")
    currency: str = Field(..., pattern="^(RUB|USD|EUR)$")
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(default={}, alias="metadata")  # поле metadata в API, но в БД называется meta
    webhook_url: HttpUrl

    class Config:
        populate_by_name = True  # разрешает использовать alias 'metadata' для поля meta

# Схема для ответа при создании (202 Accepted)
class PaymentCreateResponse(BaseModel):
    payment_id: str
    status: str
    created_at: datetime

# Схема для информации о платеже (GET)
class PaymentResponse(BaseModel):
    id: str
    amount: Decimal
    currency: str
    description: Optional[str]
    meta: Dict[str, Any] = {}
    status: str
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None