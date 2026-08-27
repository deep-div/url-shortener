from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.clients.postgresql import get_db
from app.modules.url_shortener.security import validate_url, extract_code
from app.modules.url_shortener.shorten import run_url_shortener, run_resolve_code
from app.modules.url_analytics.analytics import get_url_stats 
from app.modules.url_shortener.kafka_producer_clicks import produce_click_event
from app.modules.url_analytics.schema import UrlStatsResponse

router = APIRouter()


@router.post("/v1/shorten")
async def shorten_url(db: AsyncSession = Depends(get_db), url: str = Form(...)):
    try:
        validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        return await run_url_shortener(url, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"shorten_url failed for url={url}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")


@router.get("/{code}")
async def resolve_url(code: str, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    try:
        long_url = await run_resolve_code(code, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"resolve_url failed for code={code}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

    if not long_url:
        logger.warning(f"Short code not found: {code}")
        raise HTTPException(status_code=404, detail="Short code not found")
    background_tasks.add_task(produce_click_event, code, request)
    return RedirectResponse(url=long_url, status_code=302)


@router.get("/v1/analytics/{code}", response_model=UrlStatsResponse)
async def get_url_analytics(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    code = extract_code(code)
    try:
        return await get_url_stats(code, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_url_analytics failed for code={code}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
