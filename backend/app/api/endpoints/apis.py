from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.modules.request_processor import run_request_processor
from app.modules.url_shortner import run_url_shortener, run_resolve_code

router = APIRouter()


class ShortenRequest(BaseModel):
    url: str


@router.post("/shorten")
def shorten_url(body: ShortenRequest, request: Request):
    ip = request.client.host
    try:
        run_request_processor(ip, body.url)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base_url = str(request.base_url).rstrip("/")
    return run_url_shortener(body.url, base_url)


@router.get("/{code}")
def redirect_to_url(code: str):
    long_url = run_resolve_code(code)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=long_url, status_code=301)
