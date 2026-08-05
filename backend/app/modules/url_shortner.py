import asyncio
import secrets
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.redis import redis_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.schema import ShortenResponse
from app.repositories.url_repository import UrlRepository
from app.workers.code_pool import POOL_KEY

BASE62 = string.digits + string.ascii_letters
CODE_LEN = 7
REDIS_TTL = 60 * 60 * 24 * 30        # 30 days
REFRESH_THRESHOLD = 60 * 60 * 24 * 7  # refresh only if < 7 days remaining
BASE_URL = settings.BASE_URL.rstrip("/")

# Cached URL: 1 Redis read. Can't go lower.
# New URL: 1 Redis read + 1 DB write. Can't go lower.
# Fallback: 1 Redis read + 1 DB write per attempt. Same.

class UrlShortener:

    def __init__(self, session: AsyncSession):
        self.repo = UrlRepository(session)

    async def generate_short_code(self, url: str, cached_code: str | None = None, cached_ttl: int = -1) -> ShortenResponse:
        # check Redis cache — fastest path, no DB touch
        existing_code = cached_code or await redis_client.get(f"url:{url}")
        if existing_code:
            if cached_ttl != -1 and cached_ttl < REFRESH_THRESHOLD:
                asyncio.create_task(_refresh_ttl(existing_code, url))
            return ShortenResponse(code=existing_code, short_url=f"{BASE_URL}/{existing_code}")

        # Skip SELECT — attempt write directly, saves one DB round-trip for new URLs
        fallback_reason = None
        code = await redis_client.lpop(POOL_KEY)

        if not code:
            fallback_reason = "pool_empty"

        if code:
            short_url = f"{BASE_URL}/{code}"
            try:
                 # if url is there i update same url and return same code 
                row, existed = await self.repo.save_or_get(code, url, short_url)
                if existed:
                    return await self.cache_and_return(row)
            except IntegrityError:
                fallback_reason = "pool_code_collision"
                code = None

        ## Fallback
        if not code:
            logger.warning(f"Fallback because {fallback_reason} for {url}")
            while True:
                code = self._random_code()
                short_url = f"{BASE_URL}/{code}"
                try:
                    row, existed = await self.repo.save_or_get(code, url, short_url)
                    if existed:
                        return await self.cache_and_return(row)
                    break
                except IntegrityError:
                    continue

        pipe = redis_client.pipeline()
        pipe.set(f"url:{url}", code, ex=REDIS_TTL)
        pipe.set(f"code:{code}", url, ex=REDIS_TTL)
        await pipe.execute()

        return ShortenResponse(code=code, short_url=short_url)

    async def cache_and_return(self, row) -> ShortenResponse:
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
                asyncio.create_task(_refresh_ttl(code, existing))  # expire runs after response sent
            return existing

        # cache miss — check PostgreSQL
        row = await self.repo.get_by_code(code)
        if row:
            await redis_client.set(f"code:{code}", row.long_url, ex=REDIS_TTL)
            return row.long_url

        return None

    def _random_code(self) -> str:
        return "".join(secrets.choice(BASE62) for _ in range(CODE_LEN))


async def _refresh_ttl(code: str, url: str) -> None:
    pipe = redis_client.pipeline()
    pipe.expire(f"code:{code}", REDIS_TTL)
    pipe.expire(f"url:{url}", REDIS_TTL)
    await pipe.execute()


async def run_url_shortener(url: str, session: AsyncSession, cached_code: str | None = None, cached_ttl: int = -1) -> ShortenResponse:
    shortener = UrlShortener(session)
    return await shortener.generate_short_code(url, cached_code, cached_ttl)


async def run_resolve_code(code: str, session: AsyncSession) -> str | None:
    shortener = UrlShortener(session)
    return await shortener.resolve_code(code)
