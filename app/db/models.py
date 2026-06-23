# app/db/models.py
import uuid
from sqlalchemy import Column, String, Numeric, DateTime, JSON, Integer, Enum, func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(Enum("RUB", "USD", "EUR", name="currency_enum"), nullable=False)
    description = Column(String, nullable=True)
    # переименовали metadata -> meta
    meta = Column(JSON, default={})
    status = Column(Enum("pending", "succeeded", "failed", name="status_enum"), default="pending")
    idempotency_key = Column(String, unique=True, nullable=False)
    webhook_url = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Outbox(Base):
    __tablename__ = "outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(Enum("pending", "sent", name="outbox_status_enum"), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    retry_count = Column(Integer, default=0)