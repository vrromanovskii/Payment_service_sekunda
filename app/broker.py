# app/broker.py
from faststream.rabbit import RabbitBroker, RabbitQueue
from app.core.config import settings

broker = RabbitBroker(settings.RABBITMQ_URL)

# Явно объявляем очереди
main_queue = RabbitQueue("payments.new")
dlq_queue = RabbitQueue("payments.dlq")