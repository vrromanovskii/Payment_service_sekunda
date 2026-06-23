# app/consumers/payment_consumer.py
import asyncio
import random
import sys
import logging
import httpx
from faststream import FastStream
from sqlalchemy import select
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.broker import broker
from app.db.database import AsyncSessionLocal
from app.db.models import Payment

# Настраиваем логирование в stdout с немедленным сбросом
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True  # Перезаписывает любые ранее установленные настройки логгера
)

logger = logging.getLogger(__name__)

@broker.subscriber("payments.new")
async def handle_payment(message: dict):
    payment_id = message["payment_id"]
    logger.info(f"Processing payment {payment_id}")

    # 1. Эмуляция задержки 2–5 сек
    await asyncio.sleep(random.uniform(2, 5))

    # 2. Эмуляция результата (90% успех)
    success = random.random() < 0.9
    #success = False
    new_status = "succeeded" if success else "failed"

    # 3. Обновление БД (с идемпотентной проверкой)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            return
        if payment.status != "pending":
            logger.info(f"Payment {payment_id} already processed (status={payment.status})")
            return

        payment.status = new_status
        await session.commit()
        await session.refresh(payment)

    # 4. Отправка webhook с ретраями (3 попытки, экспоненциальная задержка)
    webhook_url = payment.webhook_url
    payload = {
        "payment_id": payment.id,
        "status": payment.status,
        "amount": str(payment.amount),
        "currency": payment.currency,
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def send_webhook():
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
        logger.info(f"Webhook sent to {webhook_url}")

    try:
        await send_webhook()
    except Exception as e:
        logger.error(f"Webhook failed after 3 attempts: {e}")
        # Отправляем в DLQ
        await broker.publish(
            {"payment_id": payment_id, "error": str(e)},
            queue="payments.dlq"
        )
        logger.info(f"Payment {payment_id} moved to DLQ")
        #print(f"Payment {payment_id} moved to DLQ", flush=True)

# Точка входа для запуска консьюмера отдельно
app = FastStream(broker)