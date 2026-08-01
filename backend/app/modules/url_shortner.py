import secrets
import string

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.clients.redis import redis_client
from app.modules.schema import ShortenResponse
from app.repositories.url_repository import UrlRepository

BASE62 = string.digits + string.ascii_letters  
CODE_LEN = 7
REDIS_TTL = 60 * 60 * 24 * 30   # 30 days


class UrlShortener:

    def __init__(self, session: Session):
        self.repo = UrlRepository(session)

    def generate_short_code(self, url: str, base_url: str) -> ShortenResponse:
        # check Redis cache — fastest path, no DB touch
        existing_code = redis_client.get(f"url:{url}")
        if existing_code:
            redis_client.expire(f"url:{url}", REDIS_TTL)
            redis_client.expire(f"code:{existing_code}", REDIS_TTL)
            return ShortenResponse(code=existing_code, short_url=f"{base_url}/{existing_code}")

        # cache miss — check PostgreSQL
        row = self.repo.get_by_long_url(url)
        if row:
            redis_client.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
            redis_client.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
            return ShortenResponse(code=row.code, short_url=row.short_url)

        # Worst case, brand new URL — random code, retry on the rare collision
        while True:
            code = self._random_code()
            short_url = f"{base_url}/{code}"
            try:
                self.repo.save(code, url, short_url)  ## Save in postgres
                break
            except IntegrityError:
                continue

        redis_client.set(f"url:{url}", code, ex=REDIS_TTL) ## Save in Redis
        redis_client.set(f"code:{code}", url, ex=REDIS_TTL)

        return ShortenResponse(code=code, short_url=short_url)

    def resolve_code(self, code: str) -> str | None:
        # check Redis cache
        existing = redis_client.get(f"code:{code}")
        if existing:
            redis_client.expire(f"code:{code}", REDIS_TTL)
            redis_client.expire(f"url:{existing}", REDIS_TTL)
            return existing

        # cache miss — check PostgreSQL
        row = self.repo.get_by_code(code)
        if row:
            redis_client.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
            redis_client.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
            return row.long_url

        return None

    def _random_code(self) -> str:
        return "".join(secrets.choice(BASE62) for _ in range(CODE_LEN))


def run_url_shortener(url: str, base_url: str, session: Session) -> ShortenResponse:
    shortener = UrlShortener(session)
    return shortener.generate_short_code(url, base_url)


def run_resolve_code(code: str, session: Session) -> str | None:
    shortener = UrlShortener(session)
    return shortener.resolve_code(code)
