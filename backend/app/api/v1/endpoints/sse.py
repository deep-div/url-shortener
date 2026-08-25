import asyncio
import json
from contextlib import suppress

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.modules.url_analytics.broadcaster import broadcaster
from app.clients.postgresql import AsyncSessionLocal
from app.modules.url_analytics.analytics import get_url_stats, build_live_snapshot
from app.core.logging import logger

router = APIRouter()

KEEPALIVE_INTERVAL = 20  # seconds


@router.get("/v1/sse/analytics/{code}")
async def analytics_sse(code: str):
    async def event_stream():
        # Send current snapshot immediately on connect so the client is up-to-date
        try:
            async with AsyncSessionLocal() as db:
                stats = await get_url_stats(code, db)
            yield f"data: {json.dumps(build_live_snapshot(stats))}\n\n"
        except Exception as e:
            logger.warning(f"Could not send initial snapshot for code {code}: {e}")

        queue = broadcaster.subscribe(code)
        logger.info(f"SSE connected for code: {code}")

        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_INTERVAL)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    # SSE comment line — keeps the HTTP connection alive through proxies
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            broadcaster.unsubscribe(code, queue)
            logger.info(f"SSE disconnected for code: {code}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
