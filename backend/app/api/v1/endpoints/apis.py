import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.clients.postgresql import get_db
from app.modules.url_shortener.security import validate_url
from app.modules.url_shortener.shorten import run_url_shortener, run_resolve_code
from app.modules.url_analytics.analytics import get_url_stats as fetch_url_stats
from app.modules.url_shortener.kafka_producer import produce_click_event
from app.modules.url_analytics.schema import UrlStatsResponse
from app.api.v1.endpoints.utils import extract_code

router = APIRouter()


@router.post("/v1/shorten")
async def shorten_url(db: AsyncSession = Depends(get_db), url: str = Form(...)):
    try:
        validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await run_url_shortener(url, db)


@router.get("/v1/{code}")
async def resolve_url(code: str, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    long_url = await run_resolve_code(code, db)
    if not long_url:
        logger.warning(f"Short code not found: {code}")
        raise HTTPException(status_code=404, detail="Short code not found")
    background_tasks.add_task(produce_click_event, code, request)
    return {"long_url": long_url}


@router.get("/v1/analytics/{code}", response_model=UrlStatsResponse)
async def get_url_stats(
    code: str,
    db: AsyncSession = Depends(get_db),
    from_date: datetime.date | None = Query(None, alias="from"),
    to_date: datetime.date | None = Query(None, alias="to"),
):
    if from_date and not to_date:
        to_date = from_date
    return await fetch_url_stats(extract_code(code), db, from_date, to_date)
