from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_timeout=10,
    pool_recycle=1800,
    connect_args={
        "ssl": "require",
        # Required when connecting through Supabase's Supavisor pooler in
        # transaction mode (port 6543): it doesn't support server-side
        # prepared statements shared across pooled connections, so asyncpg's
        # statement cache must be disabled or every query intermittently
        # fails/misbehaves.
        "statement_cache_size": 0,
    },
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
