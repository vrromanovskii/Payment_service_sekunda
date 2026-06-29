from pydantic_settings import BaseSettings # BaseSettings нужен для чтения переменных окружения

#подтягиваем переменные из .env
class Settings(BaseSettings):
    DATABASE_URL: str
    RABBITMQ_URL: str
    API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings() #создаём экземпляр класса Settings