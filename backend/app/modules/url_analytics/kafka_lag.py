import asyncio

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.structs import TopicPartition

from app.clients.kafka import get_kafka_client
from app.core.config import settings

# (topic, group_id) pairs to report on. group_id=None means no consumer
# group reads that topic — only total message count is meaningful there.
# Same consumer groups used by kafka_consumer_db.py and kafka_consumer_redis.py
TOPIC_GROUPS = [
    (settings.KAFKA_CLICKS_TOPIC, "url-analytics-consumer"),
    (settings.KAFKA_CLICKS_TOPIC, "url-analytics-redis"),
    (settings.KAFKA_DLQ_TOPIC, None),  # dlq-log — nothing consumes it currently
]


async def _topic_partitions(topic: str) -> list[TopicPartition]:
    """AIOKafkaConsumer.partitions_for_topic() only reads the consumer's own
    cached cluster metadata, which never gets populated unless the consumer
    subscribes to the topic — and subscribing here would make this
    lag-checker join the real consumer group and risk stealing partitions /
    triggering a rebalance in production. consumer.topics() doesn't help
    either — it fetches metadata into a separate throwaway object instead of
    updating the consumer's cache, so partitions_for_topic() still returns
    None afterwards.

    AIOKafkaProducer.partitions_for() is the one official async call that
    properly fetches AND caches partition metadata for a single topic
    without ever joining a consumer group, so we use a throwaway producer
    just to resolve partition ids."""
    producer = AIOKafkaProducer(**get_kafka_client())
    await producer.start()
    try:
        partitions = await producer.partitions_for(topic)
        return [TopicPartition(topic, p) for p in sorted(partitions or [])]
    finally:
        await producer.stop()


async def _topic_group_lag(topic: str, group_id: str | None) -> dict:
    tps = await _topic_partitions(topic)

    consumer = AIOKafkaConsumer(
        **get_kafka_client(),
        group_id=group_id,
        enable_auto_commit=False,
        request_timeout_ms=5000,
    )
    await consumer.start()
    try:
        end_offsets = await consumer.end_offsets(tps)
        total_messages = sum(end_offsets.values())

        current_offset = None
        lag = None
        if group_id is not None:
            current_offset = 0
            for tp in tps:
                committed = await consumer.committed(tp)
                if committed is not None:
                    current_offset += committed
            lag = total_messages - current_offset

        return {
            "topic": topic,
            "group": group_id,
            "total_messages": total_messages,
            "current_offset": current_offset,
            "lag": lag,
        }
    finally:
        await consumer.stop()


async def get_consumer_lag() -> list[dict]:
    return await asyncio.gather(
        *[_topic_group_lag(topic, group) for topic, group in TOPIC_GROUPS]
    )
