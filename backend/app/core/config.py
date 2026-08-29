from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    REDIS_HOST: str
    REDIS_KEY: str
    REDIS_PORT: int

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    BASE_URL: str
    WORKER_ID: int = 1

    LOG_LEVEL: str
    ENVIRONMENT: str

    KAFKA_ENABLED: bool
    KAFKA_SERVICE_URI: str | None = None
    KAFKA_HOST: str | None = None
    KAFKA_PORT: int | None = None
    KAFKA_USERNAME: str | None = None
    KAFKA_PASSWORD: str | None = None
    KAFKA_CLICKS_TOPIC: str | None = None
    KAFKA_DLQ_TOPIC: str | None = None
    KAFKA_CA_CERT: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
