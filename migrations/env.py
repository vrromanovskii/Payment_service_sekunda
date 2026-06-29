import asyncio
from logging.config import fileConfig #для загрузки настроек логирования
import sys
sys.path.append('.') # добавляет корень проекта в путь поиска модулей python

from sqlalchemy import pool # для управления пулом соединений
from sqlalchemy.engine import Connection # тип соезинения
from sqlalchemy.ext.asyncio import async_engine_from_config # асинхронный движок из конфигурации

from alembic import context # context предоставляет доступ к настройкам и состоянию миграции

# импортируем настройки, чтобы взять DATABASE_URL и базовый класс моделей Base
from app.core.config import settings
from app.db.models import Base

config = context.config # получаем объект конфигурации Alembic

# Передаем URL из настроек в Alembic
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# если в конфигурации указан файл с настройками логгирования, загружаем его
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata # получаем метаданные из нашего базового класса

def run_migrations_offline() -> None: # функция для запуска миграций без подключения к базе
    url = config.get_main_option("sqlalchemy.url") # строка подключения
    context.configure( # настройка Alembic с метаданными и параметрами
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction(): # создает транзакцию и выполняет миграции
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None: # функция выполняет миграции на переданном синхронном соединении
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None: # создаём асинхронный движок из конфигурации
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # отключает пул соединений, чтобы каждое подключение создавалось заново
    )

    # Устанавливаем асинхронное соединение, затем вызываем run_sync, чтобы выполнить синхронную функцию do_run_migrations внутри асинхронного контекста. Делаем так, потому что Alembic внутри синхронный
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose() # закрываем движок и освобождаем ресурсы

def run_migrations_online() -> None: # запускаем асинхронную миграцию в синхронном контексте Alembic
    asyncio.run(run_async_migrations())

# выбираем режим в зависимости от того, запущена миграция с флагом --sql (оффлайн) или обычная (онлайн)
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()