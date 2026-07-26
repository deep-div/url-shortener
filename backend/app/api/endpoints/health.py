import datetime
import pytz

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.clients.postgresql import get_db
from app.clients.redis import redis_client

IST = pytz.timezone("Asia/Kolkata")

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    status = {"status": "ok", "timestamp": datetime.datetime.now(IST).isoformat()}

    # check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        status["postgresql"] = "ok"
    except Exception as e:
        status["postgresql"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # check Redis
    try:
        redis_client.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return status
