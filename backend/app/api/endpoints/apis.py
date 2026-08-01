from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.clients.postgresql import get_db
from app.modules.security import run_security
from app.modules.url_shortner import run_url_shortener, run_resolve_code
from app.modules.url_analytics import run_url_analytics, run_get_url_stats, run_get_dashboard
from app.modules.schema import UrlStatsResponse, DashboardResponse

router = APIRouter()


@router.post("/shorten")
async def shorten_url(request: Request, db: AsyncSession = Depends(get_db), url: str = Form(...)):
    ip = request.client.host if request.client else "unknown"
    try:
        await run_security(ip, url)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base_url = str(request.base_url).rstrip("/")
    return await run_url_shortener(url, base_url, db)


@router.get("/{code}")
async def redirect_to_url(code: str, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    long_url = await run_resolve_code(code, db)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")

    background_tasks.add_task(run_url_analytics, code, request)

    return RedirectResponse(url=long_url, status_code=302)


@router.get("/analytics/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    return await run_get_dashboard(db)


@router.get("/analytics/{code}", response_model=UrlStatsResponse)
async def get_url_stats(code: str, db: AsyncSession = Depends(get_db)):
    return await run_get_url_stats(code, db)



