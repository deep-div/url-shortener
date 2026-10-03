import asyncio
import time

from app.core.config import settings

BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

class CodeGenerator:
    """Generate unique IDs using timestamp, worker ID, and sequence bits."""

    TIMESTAMP_BITS = 29
    WORKER_ID_BITS = 5
    SEQUENCE_BITS = 7
    EPOCH = 1_735_689_600  # 2025-01-01 00:00:00 UTC
    CODE_LENGTH = 7
    MAX_ID = (62 ** CODE_LENGTH) - 1

    def __init__(self, worker_id: int) -> None:
        self.max_worker_id = (1 << self.WORKER_ID_BITS) - 1
        self.max_sequence = (1 << self.SEQUENCE_BITS) - 1

        if not 0 <= worker_id <= self.max_worker_id:
            raise ValueError(f"worker_id must be between 0 and {self.max_worker_id}")

        self.worker_id = worker_id
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = asyncio.Lock()

    def _current_timestamp(self) -> int:
        return int(time.time()) - self.EPOCH

    async def _wait_next_second(self, timestamp: int) -> int:
        while timestamp <= self.last_timestamp:
            await asyncio.sleep(0.001)
            timestamp = self._current_timestamp()
        return timestamp

    async def next_id(self) -> int:
        async with self._lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise RuntimeError("System clock moved backwards")

            if timestamp == self.last_timestamp:
                self.sequence += 1
                if self.sequence > self.max_sequence:
                    timestamp = await self._wait_next_second(timestamp)
                    self.sequence = 0
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            unique_id = (
                (timestamp << (self.WORKER_ID_BITS + self.SEQUENCE_BITS))
                | (self.worker_id << self.SEQUENCE_BITS)
                | self.sequence
            )

            if unique_id > self.MAX_ID:
                raise OverflowError("ID cannot fit into 7 Base62 characters")

            return unique_id


def _base62_encode(number: int, length: int = CodeGenerator.CODE_LENGTH) -> str:
    if number < 0:
        raise ValueError("number must be non-negative")
    result = []
    while number > 0:
        number, remainder = divmod(number, 62)
        result.append(BASE62[remainder])
    encoded = "".join(reversed(result))
    if len(encoded) > length:
        raise ValueError(f"Number cannot fit into {length} Base62 characters")
    return encoded.zfill(length)


# Module-level singleton — sequence state is preserved across calls
_generator = CodeGenerator(worker_id=settings.WORKER_ID)


async def generate_code() -> str:
    """Generate a unique 7-character short code."""
    unique_id = await _generator.next_id()
    return _base62_encode(unique_id)
