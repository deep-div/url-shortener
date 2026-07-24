import string

from sqlalchemy.exc import IntegrityError

from app.clients.redis import redis_client
from app.modules.schema import ShortenResponse
from app.repositories.url_repository import UrlRepository

BASE62 = string.digits + string.ascii_letters  # 0-9 a-z A-Z
COUNTER_START = 62 ** 4   # 14,776,336 — first encoded value is exactly 5 chars
COUNTER_KEY   = "global:url_counter"
REDIS_TTL = 60 * 60 * 24  * 1   # 1 day


class UrlShortener:

    def __init__(self):
        self.repo = UrlRepository()

    def generate_short_code(self, url: str, base_url: str) -> ShortenResponse:
        # check Redis cache — fastest path, no DB touch
        existing_code = redis_client.get(f"url:{url}")
        if existing_code:
            return ShortenResponse(code=existing_code, short_url=f"{base_url}/{existing_code}")

        # cache miss — check PostgreSQL
        row = self.repo.get_by_long_url(url)
        if row:
            redis_client.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
            redis_client.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
            return ShortenResponse(code=row.code, short_url=row.short_url)

        # brand new URL — generate a unique code, retry if counter was reset and code already exists in DB
        while True:
            counter = redis_client.incr(COUNTER_KEY)
            if counter < COUNTER_START:
                redis_client.set(COUNTER_KEY, COUNTER_START)
                counter = COUNTER_START
            code = self._encode(counter)
            short_url = f"{base_url}/{code}"
            try:
                self.repo.save(code, url, short_url)
                break
            except IntegrityError:
                continue

        # cache in Redis with TTL so next hit never touches DB
        redis_client.set(f"url:{url}", code, ex=REDIS_TTL)
        redis_client.set(f"code:{code}", url, ex=REDIS_TTL)

        return ShortenResponse(code=code, short_url=short_url)

    def resolve_code(self, code: str) -> str | None:
        # check Redis cache
        existing = redis_client.get(f"code:{code}")
        if existing:
            return existing

        # cache miss — check PostgreSQL
        row = self.repo.get_by_code(code)
        if row:
            redis_client.set(f"code:{row.code}", row.long_url, ex=REDIS_TTL)
            redis_client.set(f"url:{row.long_url}", row.code, ex=REDIS_TTL)
            return row.long_url

        return None

    def _encode(self, n: int) -> str:
        code = []
        while n:
            code.append(BASE62[n % 62])
            n //= 62
        return "".join(reversed(code))


def run_url_shortener(url: str, base_url: str) -> ShortenResponse:
    shortener = UrlShortener()
    return shortener.generate_short_code(url, base_url)


def run_resolve_code(code: str) -> str | None:
    shortener = UrlShortener()
    return shortener.resolve_code(code)
