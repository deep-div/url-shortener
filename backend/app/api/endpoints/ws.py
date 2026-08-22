import asyncio
import json
from contextlib import suppress

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.clients.broadcaster import broadcaster
from app.clients.postgresql import AsyncSessionLocal
from app.modules.url_analytics import get_url_stats, build_live_snapshot
from app.core.logging import logger

router = APIRouter()

PING_INTERVAL = 20  # seconds


@router.websocket("/v1/ws/analytics/{code}")
async def analytics_ws(websocket: WebSocket, code: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for code: {code}")

    # Send current snapshot immediately so the client is up-to-date on reconnect
    try:
        async with AsyncSessionLocal() as db:
            stats = await get_url_stats(code, db)
        await websocket.send_text(json.dumps(build_live_snapshot(stats)))
    except Exception as e:
        logger.warning(f"Could not send initial snapshot for code {code}: {e}")

    # It subscribes to the Broadcaster's in-memory queue. 
    # This creates an in-memory asyncio queue for that WebSocket and associates it with the code.
    queue = broadcaster.subscribe(code)

    async def ping_loop():
        while True:
            await asyncio.sleep(PING_INTERVAL)
            await websocket.send_text("ping")

    async def send_loop():
        while True:
            data = await queue.get()
            await websocket.send_text(data)

    async def recv_loop():
        # Never expect real client messages here — this task exists purely
        # so we notice a client-initiated disconnect immediately, instead of
        # finding out only when a later send() fails on a dead socket.
        while True:
            await websocket.receive_text()

    ping_task = asyncio.create_task(ping_loop())
    send_task = asyncio.create_task(send_loop())
    recv_task = asyncio.create_task(recv_loop())
    tasks = [ping_task, send_task, recv_task]

    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for t in done:
            exc = t.exception()
            if exc and not isinstance(exc, WebSocketDisconnect):
                raise exc
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for code {code}: {e}")
    finally:
        logger.info(f"WebSocket disconnected for code: {code}")
        for t in tasks:
            t.cancel()
        for t in tasks:
            with suppress(asyncio.CancelledError, Exception):
                await t
        broadcaster.unsubscribe(code, queue)

