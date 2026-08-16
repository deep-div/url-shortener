import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.clients.postgresql import get_db
from app.modules.security import validate_url
from app.modules.url_shortner import run_url_shortener, run_resolve_code
from app.modules.url_analytics import run_url_analytics, get_url_stats as fetch_url_stats
from app.modules.schema import UrlStatsResponse
from app.api.endpoints.utils import extract_code

router = APIRouter()


@router.post("/v1/shorten")
async def shorten_url(db: AsyncSession = Depends(get_db), url: str = Form(...)):
    try:
        validate_url(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await run_url_shortener(url, db)


@router.get("/{code}")
async def redirect_to_url(code: str, db: AsyncSession = Depends(get_db)):
    long_url = await run_resolve_code(code, db)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")

    html = f"""<!doctype html>
<html>
<head><title>Redirecting...</title></head>
<body>
<script>
(function () {{
  var code = {code!r};
  fetch("https://api.ipify.org?format=json")
    .catch(function() {{ return {{ip: ""}}; }})
    .then(function(r) {{ return r.json ? r.json() : r; }})
    .then(function(data) {{
      var ipv4 = data.ip || "";
      return fetch("/v1/resolve/" + code + "?ipv4=" + encodeURIComponent(ipv4));
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(data) {{ window.location.replace(data.long_url); }})
    .catch(function() {{ window.location.replace({long_url!r}); }});
}})();
</script>
</body>
</html>"""

    return HTMLResponse(content=html)


@router.get("/v1/resolve/{code}")
async def resolve_url(code: str, request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    long_url = await run_resolve_code(code, db)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")

    background_tasks.add_task(run_url_analytics, code, request)

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
