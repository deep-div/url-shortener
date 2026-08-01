import secrets
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.redis import redis_client
from app.modules.schema import ShortenResponse
from app.repositories.url_repository import UrlRepository

BASE62 = string.digits + string.ascii_letters  
CODE_LEN = 7
REDIS_TTL = 60 * 60 * 24 * 30   # 30 days


class UrlShortener:

    def __init__(self, session: AsyncSession):
        self.repo = UrlRepository(session)

    async def generate_short_code(self, url: str, base_url: str, cached_code: str | None = None) -> ShortenResponse:
        # check Redis cache — fastest path, no DB touch
        existing_code = cached_code or await redis_client.get(f"url:{url}")
        if existing_code:
            pipe = redis_client.pipeline()
            pipe.expire(f"url:{url}", REDIS_TTL)
            pipe.expire(f"code:{existing_code}", REDIS_TTL)
            await pipe.execute()
            return ShortenResponse(code=existing_code, short_url=f"{base_url}/{existing_code}")

        # cache miss — check PostgreSQL
        row = await self.repo.get_by_long_url(url)
        if row:
            pipe = redis_client.pipeline()
            pipe.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
            pipe.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
            await pipe.execute()
            return ShortenResponse(code=row.code, short_url=row.short_url)

        # Worst case, brand new URL — random code, retry on the rare collision
        while True:
            code = self._random_code()
            short_url = f"{base_url}/{code}"
            try:
                await self.repo.save(code, url, short_url)
                break
            except IntegrityError:
                continue

        pipe = redis_client.pipeline()
        pipe.set(f"url:{url}", code, ex=REDIS_TTL)
        pipe.set(f"code:{code}", url, ex=REDIS_TTL)
        await pipe.execute()

        return ShortenResponse(code=code, short_url=short_url)

    async def resolve_code(self, code: str) -> str | None:
        # check Redis cache
        existing = await redis_client.get(f"code:{code}")
        if existing:
            pipe = redis_client.pipeline()
            pipe.expire(f"code:{code}", REDIS_TTL)
            pipe.expire(f"url:{existing}", REDIS_TTL)
            await pipe.execute()
            return existing

        # cache miss — check PostgreSQL
        row = await self.repo.get_by_code(code)
        if row:
            pipe = redis_client.pipeline()
            pipe.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
            pipe.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
            await pipe.execute()
            return row.long_url

        return None

    def _random_code(self) -> str:
        return "".join(secrets.choice(BASE62) for _ in range(CODE_LEN))


async def run_url_shortener(url: str, base_url: str, session: AsyncSession, cached_code: str | None = None) -> ShortenResponse:
    shortener = UrlShortener(session)
    return await shortener.generate_short_code(url, base_url, cached_code)


async def run_resolve_code(code: str, session: AsyncSession) -> str | None:
    shortener = UrlShortener(session)
    return await shortener.resolve_code(code)
