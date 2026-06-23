from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Создаем движок
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Полезно для отладки SQL-запросов в консоли
    future=True
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Зависимость для FastAPI (чтобы получать сессию в эндпоинтах)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session