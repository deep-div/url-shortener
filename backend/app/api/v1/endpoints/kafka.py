from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.logging import logger
from app.modules.url_analytics.kafka_lag import get_consumer_lag

router = APIRouter()


@router.get("/v1/kafka/lag")
async def kafka_lag():
    if not settings.KAFKA_ENABLED:
        raise HTTPException(status_code=503, detail="Kafka is disabled (KAFKA_ENABLED=False)")

    try:
        return await get_consumer_lag()
    except Exception as e:
        logger.error(f"kafka_lag failed: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Failed to fetch Kafka consumer lag")
