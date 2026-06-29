# импортируем асинхронную сессию и функцию select для построения SQL-запросов
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# импортируем модели таблиц
from app.db.models import Payment, Outbox
# импортируем Pydantic-схему для валидированных входных данных
from app.schemas.payment import PaymentCreate
import uuid
from datetime import datetime


# асинхронная функция, которая создаёт новый платеж или возвращает существующий при повторном запросе
async def create_payment(db: AsyncSession, payment_data: PaymentCreate, idempotency_key: str) -> Payment:
    # Проверяем, нет ли уже платежа с таким idempotency_key
    existing = await db.execute(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    ) # выполняем SQL-запрос
    existing_payment = existing.scalar_one_or_none() #возвращает объект или None, если ничего не нашел
    if existing_payment:
        return existing_payment  # возвращаем существующий, не создаём новый

    # Создаём новый платеж, если ключ новый
    payment = Payment(
        id=str(uuid.uuid4()),
        amount=payment_data.amount,
        currency=payment_data.currency,
        description=payment_data.description,
        meta=payment_data.meta,  # сохраняем как meta
        status="pending",
        idempotency_key=idempotency_key,
        webhook_url=str(payment_data.webhook_url)
    )
    db.add(payment)
    await db.flush()  # чтобы получить id (но не коммитим)

    # Создаём запись в outbox
    outbox = Outbox(
        event_type="payment.created",
        payload={"payment_id": payment.id},
        status="pending"
    )
    db.add(outbox)

    # Коммитим транзакцию — гарантия, что либо всё сохранится, либо ничего
    await db.commit()
    await db.refresh(payment)  # обновляем объект (например, для created_at)

    return payment

# функция получения платежа по ID
async def get_payment(db: AsyncSession, payment_id: str) -> Payment | None:
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    return result.scalar_one_or_none()