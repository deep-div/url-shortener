import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_analytics.analytics import run_url_analytics_redis

BATCH_SIZE = 50
BATCH_TIMEOUT_SECS = 2


async def start_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_CLICKS_TOPIC,
        **kafka_client,
        group_id="url-analytics-redis",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    logger.info("Kafka Redis consumer started")

    try:
        buffer = []
        deadline = None

        while True:
            remaining_ms = max(0, int((deadline - asyncio.get_event_loop().time()) * 1000)) if deadline else BATCH_TIMEOUT_SECS * 1000

            records = await consumer.getmany(
                timeout_ms=remaining_ms,
                max_records=BATCH_SIZE - len(buffer),
            )
            for msgs in records.values():
                buffer.extend(msg.value for msg in msgs)

            if buffer and deadline is None:
                deadline = asyncio.get_event_loop().time() + BATCH_TIMEOUT_SECS

            time_up = deadline is not None and asyncio.get_event_loop().time() >= deadline
            batch_full = len(buffer) >= BATCH_SIZE

            if buffer and (time_up or batch_full):
                reason = "batch_full" if batch_full else "time_up"
                logger.info(f"Redis consumer flushing {len(buffer)} events — reason: {reason}")
                try:
                    await run_url_analytics_redis(buffer)
                    await consumer.commit()
                except Exception as e:
                    logger.error(f"Redis consumer batch failed — skipping, PostgreSQL is source of truth. Error: {e}", exc_info=True)
                    await consumer.commit()
                finally:
                    buffer = []
                    deadline = None

    finally:
        await consumer.stop()
        logger.info("Kafka Redis consumer stopped")
