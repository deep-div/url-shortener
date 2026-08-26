import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.clients.redis import redis_client
from app.core.logging import logger

router = APIRouter()


async def _event_stream(code: str):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"updates:{code}")
    logger.info(f"SSE client subscribed to updates:{code}")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=30)
            if message and message["type"] == "message":
                yield f"event: click\ndata: {message['data']}\n\n"
            else:
                yield f": heartbeat\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(f"updates:{code}")
        await pubsub.close()
        logger.info(f"SSE client disconnected from updates:{code}")


@router.get("/v1/analytics/live/{code}")
async def live_analytics(code: str):
    return StreamingResponse(
        _event_stream(code),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
