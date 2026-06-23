import asyncio
from app.consumers.payment_consumer import app

if __name__ == "__main__":
    asyncio.run(app.run())