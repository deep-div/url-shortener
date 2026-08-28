import asyncio
import datetime
import json
from aiokafka import AIOKafkaConsumer
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_analytics.analytics import run_url_analytics_batch
from app.modules.url_analytics.kafka_producer_dlq import send_to_dlq

BATCH_SIZE = 8500
BATCH_TIMEOUT_SECS = 5


async def start_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.KAFKA_CLICKS_TOPIC,
        **kafka_client,
        group_id="url-analytics-consumer",
        group_instance_id=f"url-analytics-consumer-{settings.WORKER_ID}",
        session_timeout_ms=30000,
        heartbeat_interval_ms=10000,
        auto_offset_reset="earliest",
        enable_auto_commit=False,  # I will commit offsets myself kafka cant commit it 
        value_deserializer=lambda v: json.loads(v.decode()),
    )
    await consumer.start()
    logger.info("Kafka DB consumer started")

    try:
        buffer = []
        deadline = None  # starts only when first message arrives

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
                logger.info(f"DB consumer flushing {len(buffer)} events — reason: {reason}")
                try:
                    await run_url_analytics_batch(buffer)
                    await consumer.commit()
                except Exception as e:
                    offsets = {
                        f"partition_{tp.partition}": await consumer.position(tp)
                        for tp in consumer.assignment()
                    }
                    logger.error(
                        f"Batch failed — pushing {len(buffer)} messages to DLQ. "
                        f"Offsets: {offsets}. Error: {e}",
                        exc_info=True,
                    )
                    dlq_messages = [
                        {
                            "source_topic": settings.KAFKA_CLICKS_TOPIC,
                            "consumer_group": "url-analytics-consumer",
                            "partitions": offsets,
                            "failed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"),
                            "error": str(e),
                            "payload": payload,
                        }
                        for payload in buffer
                    ]
                    try:
                        await send_to_dlq(dlq_messages)
                        await consumer.commit()
                    except Exception:
                        logger.error(
                            f"Failed to push {len(dlq_messages)} messages to DLQ — "
                            "offsets NOT committed, messages will be reprocessed",
                            exc_info=True,
                        )
                finally:
                    buffer = []
                    deadline = None

    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")
