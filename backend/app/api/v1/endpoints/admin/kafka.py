import asyncio
from aiokafka import AIOKafkaConsumer, TopicPartition
from fastapi import APIRouter

from app.clients.kafka import kafka_client
from app.core.config import settings

router = APIRouter()

GROUP_ID = "url-analytics-consumer"


@router.get("/v1/kafka/lag")
async def get_consumer_lag():
    # Use a read-only consumer with no group to fetch end offsets only
    consumer = AIOKafkaConsumer(**kafka_client)
    await consumer.start()
    try:
        tps_dummy = [TopicPartition(settings.KAFKA_TOPIC, 0)]
        consumer.assign(tps_dummy)
        await consumer.getmany(timeout_ms=500, max_records=1)

        partitions = consumer.partitions_for_topic(settings.KAFKA_TOPIC)
        tps = [TopicPartition(settings.KAFKA_TOPIC, p) for p in sorted(partitions)]
        consumer.assign(tps)
        end_offsets = await consumer.end_offsets(tps)
    finally:
        try:
            await consumer.stop()
        except asyncio.CancelledError:
            pass

    # Fetch committed offsets for the real group — separate consumer, stops immediately
    committed_consumer = AIOKafkaConsumer(
        **kafka_client,
        group_id=GROUP_ID,
        enable_auto_commit=False,
    )
    await committed_consumer.start()
    try:
        committed_consumer.assign(tps)
        committed = {tp: (await committed_consumer.committed(tp) or 0) for tp in tps}
    finally:
        try:
            await committed_consumer.stop()
        except asyncio.CancelledError:
            pass

    lag = {f"partition_{tp.partition}": end_offsets[tp] - committed[tp] for tp in tps}
    total_messages = {f"partition_{tp.partition}": end_offsets[tp] for tp in tps}
    return {
        "total_messages": total_messages,
        "total_messages_count": sum(total_messages.values()),
        "lag": lag,
        "total_lag": sum(lag.values()),
    }
