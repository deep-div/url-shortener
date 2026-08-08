
from urllib.parse import urlparse

def _extract_code(value: str) -> str:
    """Accept a bare short code or a full short URL — return just the code."""
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https") and parsed.path:
        return parsed.path.strip("/")
    return value.strip("/")
