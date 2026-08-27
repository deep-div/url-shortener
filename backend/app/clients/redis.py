from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_KEY,
    decode_responses=True,
    ssl=True,
    max_connections=200,
)
