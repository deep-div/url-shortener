from redis.asyncio import Redis, BlockingConnectionPool
from redis.asyncio.connection import SSLConnection

from app.core.config import settings

redis_pool = BlockingConnectionPool(
    connection_class=SSLConnection,
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_KEY,
    decode_responses=True,
    max_connections=10,  # matches the Postgres pool (pool_size=5 + max_overflow=5) for consistent fd budget
    timeout=5,  # wait up to 5s for a free connection instead of raising immediately
)
redis_client = Redis(connection_pool=redis_pool)
