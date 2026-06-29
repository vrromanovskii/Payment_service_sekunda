"""Настройка и инициализация брокера сообщений"""

from faststream.rabbit import RabbitBroker, RabbitQueue
# импортируем объект settings, чтобы получить URL для подключения к RabbitMQ
from app.core.config import settings

# создаем экземпляр брокера, передавая ему строку подключения из конфигурации
broker = RabbitBroker(settings.RABBITMQ_URL)

# Явно объявляем очереди
main_queue = RabbitQueue("payments.new") # основная очередь для новых платежей, куда outbox-воркер будет публиковать события
dlq_queue = RabbitQueue("payments.dlq") # очередь для «мертвых» сообщений (DLQ), куда консьюмер будет перемещать сообщения после неудачных попыток обработки