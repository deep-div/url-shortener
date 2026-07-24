import string

from app.clients.redis import redis_client

BASE62 = string.digits + string.ascii_letters  # 0-9 a-z A-Z
MIN_LENGTH = 5

# Counter starts at 62^4 so the first encoded value is exactly 5 chars
COUNTER_START = 62 ** 4          # 14,776,336
COUNTER_KEY   = "global:url_counter"


class UrlShortener:

    def generate_short_code(self, url: str) -> str:
        existing = redis_client.get(f"url:{url}")
        if existing:
            return existing

        counter = redis_client.incr(COUNTER_KEY)

        # initialise counter to start at 5-char range on first use
        if counter < COUNTER_START:
            counter = redis_client.getset(COUNTER_KEY, COUNTER_START)
            counter = int(counter) if counter else COUNTER_START

        return self._encode(counter)

    def _encode(self, n: int) -> str:
        code = []
        while n:
            code.append(BASE62[n % 62])
            n //= 62
        return "".join(reversed(code))


def run_url_shortener(url: str) -> str:
    shortener = UrlShortener()
    return shortener.generate_short_code(url)
