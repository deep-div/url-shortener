import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router
from app.clients.geoip import init_geoip
from app.modules.url_analytics.broadcaster import broadcaster
from app.modules.url_shortener.kafka_producer import start_producer, stop_producer
from app.modules.url_analytics.kafka_consumer import start_consumer
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    init_geoip()
    await broadcaster.start()
    await start_producer()
    asyncio.create_task(start_consumer())
    yield
    logger.info("Application shutting down")
    await stop_producer()
    await broadcaster.stop()


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