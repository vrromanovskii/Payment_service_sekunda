# app/main.py
from fastapi import FastAPI
from app.api.endpoints import payments
from app.consumers.outbox_publisher import start_outbox_publisher
from app.broker import broker, main_queue, dlq_queue

app = FastAPI(title="Payment Processing Service")
app.include_router(payments.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    # 1. Подключаемся к RabbitMQ
    await broker.connect()
    await broker.declare_queue(main_queue)
    await broker.declare_queue(dlq_queue)
    # 2. Запускаем фоновую задачу публикатора
    await start_outbox_publisher()

@app.on_event("shutdown")
async def shutdown():
    await broker.close()