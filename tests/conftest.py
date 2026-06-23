import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.main import app
from app.db.database import get_db
from app.db.models import Base
from app.core.config import settings

# Тестовая БД
TEST_DATABASE_URL = settings.DATABASE_URL.replace("payments", "payments_test")

# Создаём синхронный движок для миграций (чтобы избежать конфликтов с asyncpg)
sync_engine = create_engine(TEST_DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
SyncSessionLocal = sessionmaker(sync_engine)

# Асинхронный движок для операций в тестах
async_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncTestingSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Фикстура для подготовки БД – создаём таблицы один раз (синхронно)
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(sync_engine)
    yield
    Base.metadata.drop_all(sync_engine)

# Переопределяем зависимость get_db
async def override_get_db():
    async with AsyncTestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Фикстура HTTP-клиента
@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# Фикстура сессии БД – каждый тест получает свежую сессию
@pytest_asyncio.fixture
async def db_session():
    async with AsyncTestingSessionLocal() as session:
        yield session