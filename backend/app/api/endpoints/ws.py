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
        async for message in pubsub.listen():
            if message.get("type") == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for code: {code}")
    except Exception as e:
        logger.error(f"WebSocket error for code {code}: {e}")
    finally:
        await pubsub.unsubscribe(f"analytics:{code}")
        await pubsub.aclose()
