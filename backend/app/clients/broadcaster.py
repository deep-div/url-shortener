import asyncio
from collections import defaultdict
from contextlib import suppress
from typing import Dict, Optional, Set

from app.clients.redis import redis_client
from app.core.logging import logger

CHANNEL_PATTERN = "analytics:*"
QUEUE_MAXSIZE = 100  # bounds memory if a client stops reading


class Broadcaster:
    """
    Single shared Redis pub/sub connection for the whole process.

    Instead of every WebSocket client opening its own `redis_client.pubsub()`
    connection (1 dedicated Redis connection per client - doesn't scale),
    this keeps exactly ONE `psubscribe("analytics:*")` connection open and
    fans incoming messages out to in-process asyncio.Queue objects keyed by
    url code.
    """

    def __init__(self, pattern: str = CHANNEL_PATTERN):
        self._pattern = pattern
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._pubsub = None
        self._listen_task: Optional[asyncio.Task] = None

    # start() creates a Redis Pub/Sub subscription for all analytics:* channels. 1 subscription → many channels, Pattern: analytics:*
    # psubscribe-> Pattern Subscribe
    async def start(self) -> None:
        if self._listen_task is not None:
            return
        self._pubsub = redis_client.pubsub()
        await self._pubsub.psubscribe(self._pattern)
        self._listen_task = asyncio.create_task(self._listen())
        logger.info(f"Broadcaster subscribed to {self._pattern}")

    async def stop(self) -> None:
        if self._listen_task is not None:
            self._listen_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._listen_task
            self._listen_task = None

        if self._pubsub is not None:
            with suppress(Exception):
                await self._pubsub.punsubscribe(self._pattern)
                await self._pubsub.aclose()
            self._pubsub = None

    async def _listen(self) -> None:
        try:
            async for message in self._pubsub.listen():
                if message.get("type") != "pmessage":
                    continue

                channel = message.get("channel", "")
                code = channel.split(":", 1)[-1]

                queues = self._subscribers.get(code)
                if not queues:
                    continue

                data = message["data"]
                for q in list(queues):
                    try:
                        q.put_nowait(data)
                    except asyncio.QueueFull:
                        logger.warning(f"Dropping analytics message for {code}: slow consumer")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Broadcaster listen error: {e}")

    def subscribe(self, code: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._subscribers[code].add(q)
        return q

    def unsubscribe(self, code: str, q: asyncio.Queue) -> None:
        queues = self._subscribers.get(code)
        if not queues:
            return
        queues.discard(q)
        if not queues:
            self._subscribers.pop(code, None)


broadcaster = Broadcaster()
