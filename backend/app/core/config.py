import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


def _load_vault_secrets():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Supabase Vault not configured; using local environment variables.")
        return

    try:
        from supabase import create_client

        supabase = create_client(url, key)
        rows = supabase.rpc("get_all_vault_secrets").execute().data

        for row in rows:
            os.environ.setdefault(row["name"], row["secret"])

        print(f"Loaded {len(rows)} secrets from Supabase Vault.")

    except Exception as e:
        print(f"Failed to load secrets from Supabase Vault: {e}")


_load_vault_secrets()


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

    LOG_LEVEL: str
    ENVIRONMENT: str

    class Config:
        env_file = ".env"


settings = Settings()
