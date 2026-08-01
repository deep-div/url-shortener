import time
from urllib.parse import urlparse

from app.clients.redis import redis_client

class RequestProcessor:

    RATE_LIMIT = 10
    WINDOW_SECONDS = 60

    async def check_rate_limit(self, ip: str) -> bool:
        key = f"rate:{ip}"
        now_ms = int(time.time() * 1000)
        window_start_ms = now_ms - (self.WINDOW_SECONDS * 1000)

        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start_ms)
        pipe.zcard(key)
        pipe.zadd(key, {str(now_ms): now_ms})
        pipe.expire(key, self.WINDOW_SECONDS)
        results = await pipe.execute()

        if results[1] >= self.RATE_LIMIT:
            raise PermissionError(f"IP {ip} exceeded {self.RATE_LIMIT} req/{self.WINDOW_SECONDS}s")

        return True

    def validate_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")

        if not parsed.netloc:
            raise ValueError("URL has no domain")

        return True


async def run_request_processor(ip: str, url: str):
    processor = RequestProcessor()
    await processor.check_rate_limit(ip)
    processor.validate_url(url)
