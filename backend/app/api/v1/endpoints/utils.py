
from urllib.parse import urlparse
from fastapi import HTTPException
from app.core.config import settings


def extract_code(value: str) -> str:
    """Accept a bare short code or a full short URL — return just the code.
    If a full URL is provided, it must match the configured BASE_URL domain."""
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https"):
        base = urlparse(settings.BASE_URL)
        if parsed.netloc.lower() != base.netloc.lower():
            raise HTTPException(
                status_code=400,
                detail="URL does not belong to this service's domain",
            )
        return parsed.path.strip("/")
    return value.strip("/")
