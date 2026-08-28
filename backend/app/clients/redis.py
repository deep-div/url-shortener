from redis.asyncio import Redis, BlockingConnectionPool
from redis.asyncio.connection import Connection

from app.core.config import settings

redis_pool = BlockingConnectionPool(
    connection_class=Connection,
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_KEY,
    decode_responses=True,
    max_connections=20,  
    timeout=None,  # wait indefinitely for a free connection instead of raising — no pool-exhaustion errors,
                   # but a genuine Redis outage will hang requests instead of falling back to DB
)
redis_client = Redis(connection_pool=redis_pool)
