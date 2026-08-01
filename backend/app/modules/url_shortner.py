import asyncio
import secrets
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.redis import redis_client
from app.core.logging import logger
from app.modules.schema import ShortenResponse
from app.repositories.url_repository import UrlRepository
from app.workers.code_pool import POOL_KEY

BASE62 = string.digits + string.ascii_letters
CODE_LEN = 7
REDIS_TTL = 60 * 60 * 24 * 30        # 30 days
REFRESH_THRESHOLD = 60 * 60 * 24 * 7  # refresh only if < 7 days remaining


class UrlShortener:

    def __init__(self, session: AsyncSession):
        self.repo = UrlRepository(session)

    async def generate_short_code(self, url: str, base_url: str, cached_code: str | None = None, cached_ttl: int = -1, pool_code: str | None = None) -> ShortenResponse:
        # check Redis cache — fastest path, no DB touch
        existing_code = cached_code or await redis_client.get(f"url:{url}")
        if existing_code:
            if cached_ttl != -1 and cached_ttl < REFRESH_THRESHOLD:
                pipe = redis_client.pipeline()
                pipe.expire(f"url:{url}", REDIS_TTL)
                pipe.expire(f"code:{existing_code}", REDIS_TTL)
                await pipe.execute()
            # return unused pool code back (fire-and-forget)
            if pool_code:
                asyncio.create_task(redis_client.rpush(POOL_KEY, pool_code))
            return ShortenResponse(code=existing_code, short_url=f"{base_url}/{existing_code}")

        # Use pre-fetched pool code from security pipeline (saves 1 Redis RT)
        fallback_reason = None
        code = pool_code
        if not code:
            fallback_reason = "pool_empty"

        if code:
            short_url = f"{base_url}/{code}"
            try:
                await self.repo.save(code, url, short_url)
            except IntegrityError as e:
                if "ix_urls_long_url" in str(e.orig):
                    # Cold-cache hit — URL already exists, return existing mapping
                    return await self.get_long_url(url)
                fallback_reason = "pool_code_collision"
                code = None

        ## Fallback
        if not code:
            logger.warning("shortener_fallback_to_random", extra={"reason": fallback_reason, "url": url})
            while True:
                code = self._random_code()
                short_url = f"{base_url}/{code}"
                try:
                    await self.repo.save(code, url, short_url)
                    break
                except IntegrityError as e:
                    if "ix_urls_long_url" in str(e.orig):
                        return await self.get_long_url(url)
                    continue

        pipe = redis_client.pipeline()
        pipe.set(f"url:{url}", code, ex=REDIS_TTL)
        pipe.set(f"code:{code}", url, ex=REDIS_TTL)
        asyncio.create_task(pipe.execute())

        return ShortenResponse(code=code, short_url=short_url)

    async def get_long_url(self, url: str) -> ShortenResponse:
        row = await self.repo.get_by_long_url(url)
        pipe = redis_client.pipeline()
        pipe.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
        pipe.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
        await pipe.execute()
        return ShortenResponse(code=row.code, short_url=row.short_url)

    async def resolve_code(self, code: str) -> str | None:
        # check Redis cache — 1 round-trip for GET + TTL together
        pipe = redis_client.pipeline()
        pipe.get(f"code:{code}")
        pipe.ttl(f"code:{code}")
        existing, ttl = await pipe.execute()
        if existing:
            if ttl != -1 and ttl < REFRESH_THRESHOLD:
                pipe = redis_client.pipeline()
                pipe.expire(f"code:{code}", REDIS_TTL)
                pipe.expire(f"url:{existing}", REDIS_TTL)
                await pipe.execute()
            return existing

        # cache miss — check PostgreSQL
        row = await self.repo.get_by_code(code)
        if row:
            await redis_client.set(f"code:{code}", row.long_url, ex=REDIS_TTL)
            return row.long_url

        return None

    def _random_code(self) -> str:
        return "".join(secrets.choice(BASE62) for _ in range(CODE_LEN))


async def run_url_shortener(url: str, base_url: str, session: AsyncSession, cached_code: str | None = None, cached_ttl: int = -1, pool_code: str | None = None) -> ShortenResponse:
    shortener = UrlShortener(session)
    return await shortener.generate_short_code(url, base_url, cached_code, cached_ttl, pool_code)


async def run_resolve_code(code: str, session: AsyncSession) -> str | None:
    shortener = UrlShortener(session)
    return await shortener.resolve_code(code)
