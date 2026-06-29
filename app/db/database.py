from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings # импортируем объект settings из config.py,
# чтобы получить строку подключения DATABASE_URL

# create_async_engine создаёт асинхронный движок, управляющий подключениями к БД
# AsyncSession - объект, через который выполняются запросы
# async_sessionmaker - фабрика, создающая сессии

# Создаем движок
engine = create_async_engine(
    settings.DATABASE_URL, # строка подключения
    echo=True,  # для отладки SQL-запросов в консоли
    future=True # включает использование будущего API
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine, # указываем движок
    class_=AsyncSession, # каждая сессия - экземпляр AsyncSession (а не обычная синхронная)
    expire_on_commit=False #отключаем автоматическое устаревание после коммита
)

# Зависимость для FastAPI (чтобы получать сессию в эндпоинтах)
async def get_db():
    async with AsyncSessionLocal() as session: # создает новую сессию и закрывает ее по выходу из контекста
        yield session # передает сессию в эндпоинт. После завершения работы эндпоинта
        # управление возвращается в эту функцию, и сессия закрывается