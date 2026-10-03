import json
from aiokafka import AIOKafkaProducer
from fastapi import Request
from app.clients.kafka import get_kafka_client
from app.core.config import settings
from app.core.logging import logger

_producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(
        **get_kafka_client(),
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await _producer.start()
    logger.info("Kafka producer started")


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        logger.info("Kafka producer stopped")


def _build_click_payload(code: str, request: Request) -> dict:
    ipv4 = request.query_params.get("ipv4", "").strip()
    ip_from_headers = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else None)
    )

    return {
        "code": code,
        "ipv4": ipv4,
        "ip_from_headers": ip_from_headers,
        "user_agent": request.headers.get("user-agent", ""),
    }


async def produce_click_event(code: str, request: Request) -> None:
    if not _producer:
        logger.error("Kafka producer not initialised — click event dropped")
        return

    payload = _build_click_payload(code, request)
    await _producer.send_and_wait(settings.KAFKA_CLICKS_TOPIC, payload)


async def process_click_event_direct(code: str, request: Request) -> None:
    """KAFKA_ENABLED=False path — runs the exact same DB + Redis pipeline
    that the Kafka consumers call, just inline for this one click instead of
    batched across many. Fine for low-traffic deployments, no Kafka needed."""
    from app.modules.url_analytics.analytics import (
        run_url_analytics_batch, run_url_analytics_redis,
    )

    payload = _build_click_payload(code, request)
    await run_url_analytics_batch([payload])
    await run_url_analytics_redis([payload])


async def dispatch_click_event(code: str, request: Request) -> None:
    if settings.KAFKA_ENABLED:
        await produce_click_event(code, request)
    else:
        await process_click_event_direct(code, request)
