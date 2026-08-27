from redis.asyncio import Redis, BlockingConnectionPool

from app.core.config import settings

redis_pool = BlockingConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_KEY,
    decode_responses=True,
    ssl=True,
    max_connections=200,
    timeout=5,  # wait up to 5s for a free connection instead of raising immediately
)
redis_client = Redis(connection_pool=redis_pool)
