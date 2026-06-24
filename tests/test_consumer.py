import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import select
from app.consumers.payment_consumer import handle_payment
from app.db.models import Payment
from tests.test_utils import create_payment_in_db, assert_webhook_payload

@pytest.mark.asyncio
async def test_consumer_process_success(db_session, mocker):
    # Создаём платеж в БД через хелпер
    payment = await create_payment_in_db(db_session, amount=100, currency="USD")

    # Мокаем отправку webhook (чтобы не делать реальный запрос)
    mock_post = mocker.patch("httpx.AsyncClient.post")
    mock_post.return_value = AsyncMock(status_code=200)

    # Вызываем обработчик напрямую
    await handle_payment({"payment_id": payment.id}, db_session = db_session)

    # Проверяем, что статус изменился
    result = await db_session.execute(select(Payment).where(Payment.id == payment.id))
    updated = result.scalar_one()
    assert updated.status in ("succeeded", "failed")

    # Проверяем, что webhook был вызван
    mock_post.assert_awaited()
    call_args = mock_post.call_args
    payload = call_args[1]["json"]
    assert_webhook_payload(payload, updated.status)

@pytest.mark.asyncio
async def test_consumer_webhook_retry_and_dlq(db_session, mocker):
    # Создаём платеж с webhook, который будет возвращать ошибку 500
    payment = await create_payment_in_db(
        db_session,
        amount=100,
        currency="USD",
        webhook_url="https://httpbin.org/status/500"
    )

    # Мокаем httpx, чтобы он всегда падал с ошибкой (например, ConnectionError)
    mock_post = mocker.patch("httpx.AsyncClient.post")
    mock_post.side_effect = Exception("Connection error")

    # Мокаем broker.publish для DLQ
    mock_publish = mocker.patch("app.consumers.payment_consumer.broker.publish",
                                new_callable=AsyncMock)

    await handle_payment({"payment_id": payment.id}, db_session = db_session)

    # Проверяем, что broker.publish был вызван (в DLQ)
    mock_publish.assert_called_once()
    call_args = mock_publish.call_args
    assert call_args[1]["queue"] == "payments.dlq"
    assert call_args[1]["payload"]["payment_id"] == payment.id