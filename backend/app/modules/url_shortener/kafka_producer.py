import json
from aiokafka import AIOKafkaProducer
from fastapi import Request
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger

_producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(
        **kafka_client,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await _producer.start()
    logger.info("Kafka producer started")


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        logger.info("Kafka producer stopped")


async def produce_click_event(code: str, request: Request) -> None:
    if not _producer:
        logger.error("Kafka producer not initialised — click event dropped")
        return

    ipv4 = request.query_params.get("ipv4", "").strip()
    ip_from_headers = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else None)
    )

    payload = {
        "code": code,
        "ipv4": ipv4,
        "ip_from_headers": ip_from_headers,
        "user_agent": request.headers.get("user-agent", ""),
    }

    await _producer.send_and_wait(settings.KAFKA_CLICKS_TOPIC, payload)
    logger.info(f"Click event produced for code: {code}")
