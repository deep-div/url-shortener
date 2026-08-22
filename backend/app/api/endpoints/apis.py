import datetime
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.clients.postgresql import get_db
from app.modules.security import validate_url
from app.modules.url_shortner import run_url_shortener, run_resolve_code
from app.modules.url_analytics import run_url_analytics, get_url_stats as fetch_url_stats
from app.modules.schema import UrlStatsResponse
from app.api.endpoints.utils import extract_code

router = APIRouter()


try:
    _REDIRECT_TEMPLATE = (Path(__file__).parent / "redirect.html").read_text()
except Exception as e:
    logger.error(f"Failed to load redirect.html template: {e}")
    raise

## API to Shorten URL
@router.post("/v1/shorten")
async def shorten_url(db: AsyncSession = Depends(get_db), url: str = Form(...)):
    try:
        validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await run_url_shortener(url, db)

## Just to make sure no icon comes on the new window opening in browser when user clicks
@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    raise HTTPException(status_code=404)

## API used by browser, Short URL redirects to Long URL
@router.get("/{code}")
async def redirect_to_url(code: str, db: AsyncSession = Depends(get_db)):
    long_url = await run_resolve_code(code, db)
    if not long_url:
        logger.warning(f"Short code not found: {code}")
        raise HTTPException(status_code=404, detail="Short code not found")
    html = _REDIRECT_TEMPLATE.replace("{{long_url}}", long_url).replace("{{code}}", code)
    return HTMLResponse(content=html)

# Fired by HTML to Record in DB, saves to postgre and redis 
@router.get("/v1/record/{code}")
async def record_click(code: str, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_url_analytics, code, request)
    return {}


# user opens analytics page
#   → useEffect fires → HTTP GET /v1/analytics/{code}   ← full data, clicks_by_day, link info, all time info makes a post request which sse cant take so https is needed.
#   → useAnalyticsSocket fires → GET /v1/sse/analytics/{code} ← also queries Postgres
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
