# импортируем необходимые инструменты Pydantic
from pydantic import BaseModel, Field, HttpUrl
#импорт даты
from datetime import datetime
#для аннотаций типов
from typing import Optional, Dict, Any
# для точной записи денежных сумм
from decimal import Decimal

# Определяем модель данных, которую клиент отправляет при создании платежа
class PaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Сумма платежа")
    currency: str = Field(..., pattern="^(RUB|USD|EUR)$")
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = Field(default={}, alias="metadata")
    webhook_url: HttpUrl

    class Config:
        populate_by_name = True  # разрешает использовать alias 'metadata' для поля meta

# схема описывает, что API возвращает клиенту в ответ на успешное создание платежа (код 202 Accepted)
class PaymentCreateResponse(BaseModel):
    payment_id: str
    status: str
    created_at: datetime

# схема возвращается при GET-запросе /api/v1/payments/{payment_id}, содержит полную информацию о платеже
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