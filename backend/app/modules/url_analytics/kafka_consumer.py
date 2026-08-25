import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_analytics.analytics import run_url_analytics_batch

BATCH_SIZE = 100
BATCH_TIMEOUT_MS = 5000


async def start_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC,
        **kafka_client,
        group_id="url-analytics-consumer",
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    logger.info("Kafka consumer started")

    try:
        while True:
            # blocks until BATCH_SIZE messages arrive OR BATCH_TIMEOUT_MS elapses
            records = await consumer.getmany(
                timeout_ms=BATCH_TIMEOUT_MS,
                max_records=BATCH_SIZE,
            )
            if not records:
                continue

            batch = [msg.value for msgs in records.values() for msg in msgs]
            logger.info(f"Processing batch of {len(batch)} click events")
            await run_url_analytics_batch(batch)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")


# if __name__ == "__main__":
#     asyncio.run(start_consumer())
