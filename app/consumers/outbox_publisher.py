# app/consumers/outbox_publisher.py
import asyncio
import logging
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Outbox
from app.broker import broker

logger = logging.getLogger(__name__)

async def publish_outbox_events():
    """Бесконечный цикл: читает outbox и отправляет в RabbitMQ."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Выбираем все pending записи
                result = await session.execute(
                    select(Outbox).where(Outbox.status == "pending")
                )
                records = result.scalars().all()

                for record in records:
                    try:
                        await broker.publish(record.payload, queue="payments.new")
                        record.status = "sent"
                        await session.commit()
                        logger.info(f"Outbox {record.id} published")
                    except Exception as e:
                        logger.error(f"Failed to publish outbox {record.id}: {e}")
        except Exception as e:
            logger.error(f"Outbox publisher loop error: {e}")

        await asyncio.sleep(1)  # проверка каждую секунду

async def start_outbox_publisher():
    """Запускает фоновую задачу."""
    asyncio.create_task(publish_outbox_events())