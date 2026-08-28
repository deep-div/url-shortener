import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.clients.geoip import init_geoip
from app.modules.url_shortener.kafka_producer_clicks import start_producer, stop_producer
from app.modules.url_analytics.kafka_producer_dlq import start_dlq_producer, stop_dlq_producer
from app.modules.url_analytics.kafka_consumer_db import start_consumer as start_db_consumer
from app.modules.url_analytics.kafka_consumer_redis import start_consumer as start_redis_consumer
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    init_geoip()
    await start_producer()
    await start_dlq_producer()
    db_task = asyncio.create_task(start_db_consumer())
    redis_task = asyncio.create_task(start_redis_consumer())
    yield
    logger.info("Application shutting down")
    await stop_producer()
    await stop_dlq_producer()
    db_task.cancel()
    redis_task.cancel()
    await asyncio.gather(db_task, redis_task, return_exceptions=True)


app = FastAPI(title="URL Shortener", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000