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
    WORKER_ID: int

    LOG_LEVEL: str
    ENVIRONMENT: str

    KAFKA_SERVICE_URI: str
    KAFKA_HOST: str
    KAFKA_PORT: int
    KAFKA_USERNAME: str
    KAFKA_PASSWORD: str
    KAFKA_CLICKS_TOPIC: str
    KAFKA_DLQ_TOPIC: str
    KAFKA_CA_CERT: str

    class Config:
        env_file = ".env"


settings = Settings()
