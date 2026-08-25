import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_analytics.analytics import run_url_analytics_batch

BATCH_SIZE = 100
BATCH_TIMEOUT_SECS = 5


async def start_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        **kafka_client,
        group_id="url-analytics-consumer",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    logger.info("Kafka consumer started")

    try:
        buffer = []
        deadline = asyncio.get_event_loop().time() + BATCH_TIMEOUT_SECS

        while True:
            now = asyncio.get_event_loop().time()
            remaining_ms = max(0, int((deadline - now) * 1000))

            records = await consumer.getmany(
                timeout_ms=remaining_ms,
                max_records=BATCH_SIZE - len(buffer),
            )
            for msgs in records.values():
                buffer.extend(msg.value for msg in msgs)

            time_up = asyncio.get_event_loop().time() >= deadline
            batch_full = len(buffer) >= BATCH_SIZE

            if buffer and (time_up or batch_full):
                reason = "batch_full" if batch_full else "time_up"
                logger.info(f"Flushing {len(buffer)} click events — reason: {reason}")
                await run_url_analytics_batch(buffer)
                await consumer.commit()
                buffer = []
                deadline = asyncio.get_event_loop().time() + BATCH_TIMEOUT_SECS
            elif time_up:
                deadline = asyncio.get_event_loop().time() + BATCH_TIMEOUT_SECS

    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
