import time
from urllib.parse import urlparse

from app.clients.redis import redis_client
from app.workers.code_pool import POOL_KEY

RATE_LIMIT = 10
WINDOW_SECONDS = 60
    
class Security:

    async def check_rate_limit_with_cache(self, ip: str, url: str) -> tuple[str | None, int, str | None]:
        key = f"rate:{ip}"
        now_ms = int(time.time() * 1000)
        window_start_ms = now_ms - (self.WINDOW_SECONDS * 1000)

        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start_ms)
        pipe.zcard(key)                          # [1] count
        pipe.zadd(key, {str(now_ms): now_ms})
        pipe.expire(key, self.WINDOW_SECONDS)
        pipe.get(f"url:{url}")                   # [4] cached short code or None
        pipe.ttl(f"url:{url}")                   # [5] remaining TTL in seconds
        pipe.lpop(POOL_KEY)                      # [6] speculative pool code for cache-miss path
        results = await pipe.execute()

        if results[1] >= self.RATE_LIMIT:
            raise PermissionError(f"IP {ip} exceeded {self.RATE_LIMIT} req/{self.WINDOW_SECONDS}s")

        return results[4], results[5], results[6]

    def validate_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")

        if not parsed.netloc:
            raise ValueError("URL has no domain")

        return True

_security = Security()
