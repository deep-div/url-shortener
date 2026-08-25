import json
from aiokafka import AIOKafkaProducer
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger


async def send_to_dlq(messages: list[dict]) -> None:
    async with AIOKafkaProducer(
        **kafka_client,
        value_serializer=lambda v: json.dumps(v).encode(),
    ) as dlq_producer:
        for message in messages:
            await dlq_producer.send(settings.KAFKA_DLQ_TOPIC, message)
    logger.info(f"Pushed {len(messages)} messages to DLQ")
