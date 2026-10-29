import json
from aiokafka import AIOKafkaProducer
from app.clients.kafka import get_kafka_client
from app.core.config import settings
from app.core.logging import logger

_dlq_producer: AIOKafkaProducer | None = None


async def start_dlq_producer() -> None:
    global _dlq_producer
    _dlq_producer = AIOKafkaProducer(
        **get_kafka_client(),
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await _dlq_producer.start()
    logger.info("Kafka DLQ producer started")


async def stop_dlq_producer() -> None:
    global _dlq_producer
    if _dlq_producer:
        await _dlq_producer.stop()
        logger.info("Kafka DLQ producer stopped")


async def send_to_dlq(messages: list[dict]) -> None:
    if not _dlq_producer:
        logger.error(f"Kafka DLQ producer not initialised — {len(messages)} messages dropped")
        return

    for message in messages:
        await _dlq_producer.send_and_wait(settings.KAFKA_DLQ_TOPIC, message)
    logger.info(f"Pushed {len(messages)} messages to DLQ")

