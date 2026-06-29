
import asyncio #асинхронность
import logging #логи
from sqlalchemy import select # select для построения SQL-запросов
from app.db.database import AsyncSessionLocal # фабрика асинхронных сессий для подключения к БД
from app.db.models import Outbox #модель таблицы outbox
from app.broker import broker # экземпляр брокера

logger = logging.getLogger(__name__) # создаем логгер

async def publish_outbox_events():
    """Бесконечный цикл: читает outbox и отправляет в RabbitMQ."""
    while True:
        try:
            async with AsyncSessionLocal() as session: # открываем асинхронную сессию для работы с БД
                # Выбираем все pending записи
                result = await session.execute(
                    select(Outbox).where(Outbox.status == "pending")
                )
                records = result.scalars().all() # возвращает список объектов Outbox, соответствующих условию

                for record in records: # для каждой записи со статусом pending
                    try:
                        await broker.publish(record.payload, queue="payments.new") # пытаемся опубликовать её payload в очередь payments.new
                        record.status = "sent" # если публикация успешна, меняем статус записи на sent
                        await session.commit() # фиксируем транзакцию
                        logger.info(f"Outbox {record.id} published") # логируем успех
                    except Exception as e: # если ошибка, логируем ошибку
                        logger.error(f"Failed to publish outbox {record.id}: {e}")
        except Exception as e: # если в самом цикле произошла ошибка, её тоже логируем
            logger.error(f"Outbox publisher loop error: {e}")

        await asyncio.sleep(1)  # проверка каждую секунду

async def start_outbox_publisher(): # запускает outbox-воркер на фоне
    """Запускает фоновую задачу."""
    asyncio.create_task(publish_outbox_events())