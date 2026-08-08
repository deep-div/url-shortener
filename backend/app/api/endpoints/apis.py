import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.clients.postgresql import get_db
from app.modules.security import _security
from app.modules.url_shortner import run_url_shortener, run_resolve_code
from app.modules.url_analytics import run_url_analytics, get_url_stats as fetch_url_stats
from app.modules.schema import UrlStatsResponse
from app.api.endpoints.utils import _extract_code

router = APIRouter()


@router.post("/v1/shorten")
async def shorten_url(request: Request, db: AsyncSession = Depends(get_db), url: str = Form(...)):
    ip = request.client.host if request.client else "unknown"

    try:
        _security.validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        cached_code, cached_ttl = await _security.check_rate_limit_with_cache(ip, url)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))

    return await run_url_shortener(url, db, cached_code, cached_ttl)


@router.get("/{code}")
async def redirect_to_url(code: str, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    long_url = await run_resolve_code(code, db)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")

    background_tasks.add_task(run_url_analytics, code, request)

    return RedirectResponse(url=long_url, status_code=302)


@router.get("/v1/analytics/{code}", response_model=UrlStatsResponse)
async def get_url_stats(
    code: str,
    db: AsyncSession = Depends(get_db),
    from_date: datetime.date | None = Query(None, alias="from"),
    to_date: datetime.date | None = Query(None, alias="to"),
):
    if from_date and not to_date:
        to_date = from_date
    return await fetch_url_stats(_extract_code(code), db, from_date, to_date)



