import datetime
import pytz

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.clients.postgresql import get_db
from app.clients.redis import redis_client

IST = pytz.timezone("Asia/Kolkata")

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    status = {"status": "ok", "timestamp": datetime.datetime.now(IST).isoformat()}

    # check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        status["postgresql"] = "ok"
    except Exception as e:
        status["postgresql"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # check Redis
    try:
        await redis_client.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return status
