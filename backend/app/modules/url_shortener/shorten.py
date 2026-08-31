import asyncio

from redis.asyncio.lock import Lock
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.redis import redis_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_shortener.schema import ShortenResponse
from app.modules.url_shortener.generate_code import generate_code
from app.modules.url_shortener.repository import UrlRepository

REDIS_TTL = 60 * 60 * 24 * 365
BASE_URL = settings.BASE_URL.rstrip("/")

## Generate code 
# 1. URL exists in Redis → 0 DB, 1 Redis command, 1 Redis round trip
# 2. URL not in Redis, URL exists in DB → 1 DB, 2 Redis commands, 1 Redis round trip
# 3. URL not in Redis, new URL, code generated successfully → 1 DB, 2 Redis commands, 1 Redis round trip
# 4. URL not in Redis, new URL, code collision once → 1 DB + 1 DB retry, 2 Redis commands, 1 Redis round trip
# 5. URL not in Redis, new URL, N code collisions → N+1 DB attempts, 2 Redis commands, 1 Redis round trip


## Resolve code 
# 1. Code exists in Redis → 0 DB, 1 Redis command, 1 Redis round trip
# 2. Code not in Redis, code exists in DB → 1 DB, 2 Redis commands, 1 Redis round trip
# 3. Code not in Redis, code does not exist in DB → 1 DB, 0 Redis commands, 0 Redis round trip

class UrlShortener:

    def __init__(self, session: AsyncSession):
        self.repo = UrlRepository(session)

    async def generate_short_code(self, url: str) -> ShortenResponse:
        existing_code = await _get_cache(f"url:{url}")

        if existing_code:
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
        # check Redis cache
        existing = await _get_cache(f"code:{code}")

        if existing:
            return existing

        return await self._resolve_stampede_guard(code)

    async def _resolve_stampede_guard(self, code: str) -> str | None:
        lock = Lock(redis_client, f"lock:code:{code}", timeout=10, blocking_timeout=10)

        try:
            acquired = await lock.acquire()
        except RedisError as e:
            logger.warning(f"Redis unavailable while acquiring stampede lock for code={code}, falling back to direct DB read. Error: {e}")
            return await self._db_read(code)

        if acquired:
            try:
                existing = await _get_cache(f"code:{code}")
                if existing:
                    return existing
                return await self._db_read_and_cache(code)
            finally:
                try:
                    await lock.release()
                except RedisError as e:
                    logger.warning(f"Redis unavailable while releasing stampede lock for code={code}. Error: {e}")

        # Didn't get the lock in time — the rebuild should be done (or nearly done) by now.
        existing = await _get_cache(f"code:{code}")
        if existing:
            return existing
        return await self._db_read(code)

    async def _db_read(self, code: str) -> str | None:
        row = await self.repo.get_by_code(code)
        if row:
            return row.long_url

        logger.warning(f"Code not found in cache or DB: {code}")
        return None

    async def _db_read_and_cache(self, code: str) -> str | None:
        row = await self.repo.get_by_code(code)
        if not row:
            logger.warning(f"Code not found in cache or DB: {code}")
            return None

        await _set_cache(row.long_url, code)
        return row.long_url


async def _get_cache(key: str, ttl: int = REDIS_TTL) -> str | None:
    try:
        # GETEX reads the value and restates its TTL in one round trip, so
        return await redis_client.getex(key, ex=ttl)
    except RedisError as e:
        logger.warning(f"Redis unavailable while reading {key}, falling back to DB. Error: {e}")
        return None


async def _set_cache(url: str, code: str, ttl: int = REDIS_TTL) -> None:
    try:
        pipe = redis_client.pipeline()
        pipe.set(f"url:{url}", code, ex=ttl)
        pipe.set(f"code:{code}", url, ex=ttl)
        await pipe.execute()
    except RedisError as e:
        logger.warning(f"Redis unavailable while caching code={code}, url={url}. Error: {e}")


async def run_url_shortener(url: str, session: AsyncSession) -> ShortenResponse:
    shortener = UrlShortener(session)
    return await shortener.generate_short_code(url)


async def run_resolve_code(code: str, session: AsyncSession) -> str | None:
    shortener = UrlShortener(session)
    return await shortener.resolve_code(code)
