import asyncio
import secrets
import string

from app.clients.redis import redis_client
from app.core.logging import logger

POOL_KEY = "code:pool"
POOL_TARGET = 500       # codes to keep ready
POOL_THRESHOLD = 200    # refill when pool drops below this
CODE_ALPHABET = string.digits + string.ascii_letters
CODE_LEN = 7
CHECK_INTERVAL = 30000     # seconds between pool size checks


async def _fill_pool() -> None:
    current = await redis_client.llen(POOL_KEY)
    if current >= POOL_THRESHOLD:
        return

    needed = POOL_TARGET - current
    codes = [
        "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
        for _ in range(needed)
    ]

    # Batch push in one pipeline round-trip
    pipe = redis_client.pipeline()
    for code in codes:
        pipe.rpush(POOL_KEY, code)
    await pipe.execute()

    logger.info("code_pool_refilled", extra={"added": needed, "total": POOL_TARGET})


async def run_code_pool_worker() -> None:
    logger.info("code_pool_worker_started")
    # Fill immediately on startup so the pool is ready before the first request
    try:
        await _fill_pool()
    except Exception:
        logger.exception("code_pool_initial_fill_error")

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        try:
            await _fill_pool()
        except Exception:
            logger.exception("code_pool_worker_error")
