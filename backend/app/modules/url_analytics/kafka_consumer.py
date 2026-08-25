import asyncio
import json
from aiokafka import AIOKafkaConsumer
from app.clients.kafka import kafka_client
from app.core.config import settings
from app.core.logging import logger
from app.modules.url_analytics.analytics import run_url_analytics


class _ClickClient:
    def __init__(self, host: str):
        self.host = host


class ClickRequest:
    """Reconstructs just enough of a FastAPI Request for parse_click_data."""

    def __init__(self, ipv4: str, ip_from_headers: str, user_agent: str):
        self.query_params = {"ipv4": ipv4}
        self.headers = {
            "x-forwarded-for": ip_from_headers,
            "user-agent": user_agent,
        }
        self.client = _ClickClient(host=ip_from_headers)


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
        async for message in consumer:
            payload = message.value
            try:
                code = payload["code"]
                fake_request = ClickRequest(
                    ipv4=payload.get("ipv4", ""),
                    ip_from_headers=payload.get("ip_from_headers", ""),
                    user_agent=payload.get("user_agent", ""),
                )
                await run_url_analytics(code, fake_request)
            except Exception as e:
                logger.error(f"Failed to process click event: {e}", exc_info=True)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer stopped")


if __name__ == "__main__":
    asyncio.run(start_consumer())
