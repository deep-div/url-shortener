import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.workers.code_pool import run_code_pool_worker
from app.clients.geoip import init_geoip
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    init_geoip()
    task = asyncio.create_task(run_code_pool_worker())
    yield
    logger.info("Application shutting down")
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


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