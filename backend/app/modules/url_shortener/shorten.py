import asyncio

from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.redis import redis_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_shortener.schema import ShortenResponse
from app.modules.url_shortener.generate_code import generate_code
from app.modules.url_shortener.repository import UrlRepository

REDIS_TTL = 60 * 60 * 24 * 30        # 30 days
REFRESH_THRESHOLD = 60 * 60 * 24 * 7  # refresh only if < 7 days remaining
BASE_URL = settings.BASE_URL.rstrip("/")

## Generate code 
# 1. URL exists in Redis, TTL > 7 days → 0 DB, 2 Redis commands, 1 Redis round trip
# 2. URL exists in Redis, TTL < 7 days → 0 DB, 4 Redis commands, 2 Redis round trips
# 3. URL not in Redis, URL exists in DB → 1 DB, 4 Redis commands, 2 Redis round trips
# 4. URL not in Redis, new URL, code generated successfully → 1 DB, 2 Redis commands, 1 Redis round trip
# 5. URL not in Redis, new URL, code collision once → 1 DB + 1 DB retry, 2 Redis commands, 1 Redis round trip
# 6. URL not in Redis, new URL, N code collisions → N+1 DB attempts, 2 Redis commands, 1 Redis round trip


## Resolve code 
# 1. Code exists in Redis, TTL > 7 days → 0 DB, 2 Redis commands, 1 Redis round trip
# 2. Code exists in Redis, TTL < 7 days → 0 DB, 4 Redis commands, 2 Redis round trips
# 3. Code not in Redis, code exists in DB → 1 DB, 4 Redis commands, 2 Redis round trips
# 4. Code not in Redis, code does not exist in DB → 1 DB, 2 Redis commands, 1 Redis round trip
# 5. Redis hit, but TTL = -1 → 0 DB, 2 Redis commands, 1 Redis round trip

class UrlShortener:

    def __init__(self, session: AsyncSession):
        self.repo = UrlRepository(session)

    async def generate_short_code(self, url: str) -> ShortenResponse:
        existing_code, cached_ttl = await _get_with_ttl(f"url:{url}")

        if existing_code:
            if cached_ttl != -1 and cached_ttl < REFRESH_THRESHOLD:
                asyncio.create_task(_refresh_ttl(existing_code, url))
            return ShortenResponse(code=existing_code, short_url=f"{BASE_URL}/{existing_code}")

        attempt = 0
        while True:
            code = await generate_code()
            short_url = f"{BASE_URL}/{code}"
            try:
                row, existed = await self.repo.save_or_get(code, url, short_url)
                if existed:
                    return await self.cache_and_return(row)
                break
            except IntegrityError:
                attempt += 1
                logger.error(f"Code collision on attempt {attempt}: code={code}, url={url}")

        await _set_cache(url, code)

        return ShortenResponse(code=code, short_url=short_url)

    async def cache_and_return(self, row) -> ShortenResponse:
        asyncio.create_task(_set_cache(row.long_url, row.code))
        return ShortenResponse(code=row.code, short_url=row.short_url)

    async def resolve_code(self, code: str) -> str | None:
        # check Redis cache — 1 round-trip for GET + TTL together
        existing, ttl = await _get_with_ttl(f"code:{code}")

        if existing:
            if ttl != -1 and ttl < REFRESH_THRESHOLD:
                asyncio.create_task(_refresh_ttl(code, existing))  # expire runs after response sent
            return existing

        # cache miss (or Redis unavailable) — PostgreSQL is the source of truth
        logger.warning(f"Redis cache miss for code: {code}, falling back to DB")
        row = await self.repo.get_by_code(code)
        if row:
            asyncio.create_task(_set_cache(row.long_url, code))
            return row.long_url

        logger.warning(f"Code not found in cache or DB: {code}")
        return None


async def _get_with_ttl(key: str) -> tuple[str | None, int | None]:
    try:
        pipe = redis_client.pipeline()
        pipe.get(key)
        pipe.ttl(key)
        return await pipe.execute()
    except RedisError as e:
        logger.warning(f"Redis unavailable while reading {key}, falling back to DB. Error: {e}")
        return None, None


async def _set_cache(url: str, code: str, ttl: int = REDIS_TTL) -> None:
    try:
        pipe = redis_client.pipeline()
        pipe.set(f"url:{url}", code, ex=ttl)
        pipe.set(f"code:{code}", url, ex=ttl)
        await pipe.execute()
    except RedisError as e:
        logger.warning(f"Redis unavailable while caching code={code}, url={url}. Error: {e}")


async def _refresh_ttl(code: str, url: str, ttl: int = REDIS_TTL) -> None:
    try:
        pipe = redis_client.pipeline()
        pipe.expire(f"code:{code}", ttl)
        pipe.expire(f"url:{url}", ttl)
        await pipe.execute()
    except RedisError as e:
        logger.warning(f"Redis unavailable while refreshing TTL for code={code}, url={url}. Error: {e}")


async def run_url_shortener(url: str, session: AsyncSession) -> ShortenResponse:
    shortener = UrlShortener(session)
    return await shortener.generate_short_code(url)


async def run_resolve_code(code: str, session: AsyncSession) -> str | None:
    shortener = UrlShortener(session)
    return await shortener.resolve_code(code)
