from urllib.parse import urlparse


def validate_url(url: str) -> None:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")

    if not parsed.netloc:
        raise ValueError("URL has no domain")
