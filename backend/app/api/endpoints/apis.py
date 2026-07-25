from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.clients.postgresql import get_db
from app.modules.request_processor import run_request_processor
from app.modules.url_shortner import run_url_shortener, run_resolve_code

router = APIRouter()


@router.post("/shorten")
def shorten_url(request: Request, db: Session = Depends(get_db), url: str = Form(...)):
    ip = request.client.host if request.client else "unknown"
    try:
        run_request_processor(ip, url)
    except PermissionError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base_url = str(request.base_url).rstrip("/")
    return run_url_shortener(url, base_url, db)


@router.get("/{code}")
def redirect_to_url(code: str, db: Session = Depends(get_db)):
    long_url = run_resolve_code(code, db)
    if not long_url:
        raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url=long_url, status_code=301)
