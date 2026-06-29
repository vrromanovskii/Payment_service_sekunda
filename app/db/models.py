# app/db/models.py
import uuid # модуль генерации уникальных идентификаторов

# импортируем столбцы и типы данных
from sqlalchemy import Column, String, Numeric, DateTime, JSON, Integer, Enum, func

# импортируем DeclarativeBase для объявления базового класса моделей
from sqlalchemy.orm import DeclarativeBase

# создаем базвый класс для всех моделей
class Base(DeclarativeBase):
    pass

class Payment(Base): # модель Payment, таблица payments
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Numeric(10, 2), nullable=False) # число с 10 знаками, 2 из которых после запятой. Не NULL
    currency = Column(Enum("RUB", "USD", "EUR", name="currency_enum"), nullable=False) #обязательное поле
    description = Column(String, nullable=True) # описание платежа. Опционально
    meta = Column(JSON, default={}) #дополнительные метаданные в формате JSON (например, {"user_id": 123})
    status = Column(Enum("pending", "succeeded", "failed", name="status_enum"), default="pending") # статус платежа
    idempotency_key = Column(String, unique=True, nullable=False) # ключ идемпотентности для защиты от повторных запросов
    webhook_url = Column(String, nullable=False) # URL для отправки увведомления
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Outbox(Base): # модель Outbox, таблица outbox
    __tablename__ = "outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False) # тип события. Например, payment.created
    payload = Column(JSON, nullable=False) # полезная нагрузка события в формате JSON. Содержит данные, которые нужно отправить в RabbitMQ (например, {"payment_id": "..."})
    status = Column(Enum("pending", "sent", name="outbox_status_enum"), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    retry_count = Column(Integer, default=0) # количество попыток отправки