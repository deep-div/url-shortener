from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    REDIS_HOST: str
    REDIS_KEY: str
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env"


settings = Settings()
