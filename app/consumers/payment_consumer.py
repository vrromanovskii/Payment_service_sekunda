import asyncio
import random
import logging
import httpx
from faststream import FastStream # для создания приложения-консьюмера
from sqlalchemy import select #для запросов БД
from sqlalchemy.ext.asyncio import AsyncSession # для БД
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type # для реализации повторных попыток


from app.broker import broker, main_queue  # брокер
from app.db.database import AsyncSessionLocal # фабрика сессий
from app.db.models import Payment # модель платежа

logger = logging.getLogger(__name__) # создаем логгер


@broker.subscriber(main_queue) # слушаем очередь, при поступлении сообщений вызываем функцию
async def handle_payment(payment_id: str, db_session: AsyncSession = None):
    #извлекаем id платежа и логируем начало обработки
    logger.info(f"Processing payment {payment_id}")

    # Эмуляция задержки 2–5 сек
    await asyncio.sleep(random.uniform(2, 5))

    # Эмуляция результата (90% успех)
    success = random.random() < 0.9
    new_status = "succeeded" if success else "failed"

    async def _process(session: AsyncSession):
        # Обновление БД (с идемпотентной проверкой)
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        ) # ищем платеж по id
        payment = result.scalar_one_or_none()
        if not payment: # если не нашли, логируем и выходим
            logger.error(f"Payment {payment_id} not found")
            return
        if payment.status != "pending": # если статус не pending, выходим
            logger.info(f"Payment {payment_id} already processed (status={payment.status})")
            return
        # если всё ок, обновляем статус, коммитим, обновляем объект
        payment.status = new_status
        await session.commit()
        await session.refresh(payment)

        # Отправка webhook с ретраями (3 попытки, экспоненциальная задержка)
        webhook_url = payment.webhook_url
        payload = { # подготавливаем данные для отправки на webhook
            "payment_id": payment.id,
            "status": payment.status,
            "amount": str(payment.amount),
            "currency": payment.currency,
        }

        @retry(
            stop=stop_after_attempt(3), # макс 3 попытки
            wait=wait_exponential(multiplier=1, min=1, max=10), #экспоненциальные задержки с ограничением 10сек
            retry=retry_if_exception_type(Exception), #повторяем при любом исключении
            reraise=True # после исчерпания попыток пробрасываем последнее исключение
        )
        async def send_webhook(): # функция для отправки на webhook с декоратором retry
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload) # отправляем post-запрос
                resp.raise_for_status() # вызывает исключение, если статус ответа >= 400
            logger.info(f"Webhook sent to {webhook_url}")

        try:
            await send_webhook() # вызываем send_webhook
        except Exception as e: # если все 3 попытки не удались, ловим исключение
            logger.error(f"Webhook failed after 3 attempts: {e}")
            # Отправляем в DLQ
            try:
                await broker.publish( # пытаемся опубликовать сообщение в DLQ с ID платежа и текстом ошибки
                    {"payment_id": payment_id, "error": str(e)},
                    queue="payments.dlq"
                )
                logger.info(f"Payment {payment_id} moved to DLQ")
            except Exception as pub_error: # если не удаётся, логируем ошибку, но дальше не пробрасываем
                logger.error(f"Failed to publish to DLQ: {pub_error}")

    # если передана сессия, используем её. Иначе открываем новую сессию через фабрику и передаём в _process
    if db_session:
        await _process(db_session)
    else:
        async with AsyncSessionLocal() as session:
            await _process(session)

# Точка входа для запуска консьюмера отдельно
app = FastStream(broker)