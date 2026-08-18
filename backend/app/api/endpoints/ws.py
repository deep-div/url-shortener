import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.clients.redis import redis_client
from app.core.logging import logger

router = APIRouter()


@router.websocket("/v1/ws/analytics/{code}")
async def analytics_ws(websocket: WebSocket, code: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for code: {code}")

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"analytics:{code}")

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                await websocket.send_text(message["data"])
            else:
                await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for code: {code}")
    except Exception as e:
        logger.error(f"WebSocket error for code {code}: {e}")
    finally:
        await pubsub.unsubscribe(f"analytics:{code}")
        await pubsub.aclose()
