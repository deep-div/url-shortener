from urllib.parse import urlparse


def validate_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")

    if not parsed.netloc:
        raise ValueError("URL has no domain")


def extract_code(value: str) -> str:
    """Accept either a bare short code or a full short URL and return the code."""
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return parsed.path.strip("/")
    return value.strip("/")
