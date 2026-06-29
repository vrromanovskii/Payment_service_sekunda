
from fastapi import FastAPI
from app.api.endpoints import payments
from app.consumers.outbox_publisher import start_outbox_publisher # импортируем функцию start_outbox_publisher, которая запускает фоновую задачу для мониторинга таблицы outbox и публикации событий в RabbitMQ
from app.broker import broker, main_queue, dlq_queue # импортируем экземпляр брокера и объекты очередей

app = FastAPI(title="Payment Processing Service") # создаём экземпляр FastAPI
app.include_router(payments.router) # подключаем роутер с эндпоинтами платежей к основному приложению


@app.get("/health") # эндпоинт проверки работоспособности сервиса
async def health():
    return {"status": "ok"}

@app.on_event("startup") #Декоратор @app.on_event("startup") регистрирует функцию, которая будет вызвана перед тем, как приложение начнёт принимать запросы
async def startup():
    # Подключаемся к RabbitMQ
    await broker.connect()
    await broker.declare_queue(main_queue)
    await broker.declare_queue(dlq_queue)
    # Запускаем фоновую задачу публикатора
    await start_outbox_publisher()

@app.on_event("shutdown") #Декоратор @app.on_event("shutdown") регистрирует функцию, которая будет вызвана перед остановкой приложения
async def shutdown():
    await broker.close() #закрываем соединение с RabbitMQ