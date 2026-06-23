# tests/test_utils.py
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Payment


def create_payment_payload(
        amount: float = 100.50,
        currency: str = "USD",
        description: str = "Test payment",
        metadata: Optional[Dict[str, Any]] = None,
        webhook_url: str = "https://httpbin.org/status/200"
) -> Dict[str, Any]:
    """
    Генерирует словарь данных для создания платежа (используется в API-тестах).
    """
    if metadata is None:
        metadata = {"test": True}

    return {
        "amount": amount,
        "currency": currency,
        "description": description,
        "metadata": metadata,
        "webhook_url": webhook_url
    }


async def create_payment_in_db(
        db_session: AsyncSession,
        status: str = "pending",
        webhook_url: str = "https://httpbin.org/status/200",
        idempotency_key: Optional[str] = None,
        amount: float = 100.0,
        currency: str = "USD"
) -> Payment:
    """
    Создает и сохраняет объект Payment напрямую в БД (без вызова API).
    Полезно для тестов Consumer, когда не нужно проверять API-слой.
    """
    if idempotency_key is None:
        idempotency_key = str(uuid.uuid4())

    payment = Payment(
        id=str(uuid.uuid4()),
        amount=amount,
        currency=currency,
        status=status,
        idempotency_key=idempotency_key,
        webhook_url=webhook_url,
        meta={"test": True}
    )
    db_session.add(payment)
    await db_session.commit()
    await db_session.refresh(payment)
    return payment


def assert_webhook_payload(payload: Dict[str, Any], expected_status: str):
    """
    Проверяет структуру и содержимое вебхук-уведомления.
    """
    assert "payment_id" in payload
    assert payload["status"] == expected_status
    assert "amount" in payload
    assert "currency" in payload