import atexit
import os
import unicodedata
import httpx
from app.core.logging import logger

GEOIP_DB_PATH = "geoipdb/GeoLite2-City.mmdb"

_reader = None


def init_geoip():
    global _reader
    if not os.path.exists(GEOIP_DB_PATH):
        logger.warning(f"GeoIP database not found at {GEOIP_DB_PATH}. Fallback geolocation will be disabled.")
        return
    try:
        from geoip2.database import Reader
        _reader = Reader(GEOIP_DB_PATH)
        atexit.register(_reader.close)
        logger.info("GeoIP database loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load GeoIP database: {e}")


def _geoip_lookup(ip: str) -> tuple[str | None, str | None]:
    if not _reader:
        return None, None
    try:
        response = _reader.city(ip)
        return response.country.name, response.city.name
    except Exception as e:
        logger.warning(f"GeoIP2 fallback lookup failed for {ip}: {e}")
        return None, None


def _ascii_name(name: str | None) -> str | None:
    if not name:
        return name
    return unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode("ascii") or name


async def get_location(ip: str) -> tuple[str | None, str | None, str]:
    country, city = _geoip_lookup(ip)
    if country:
        return country, city, "geoip2"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"http://ip-api.com/json/{ip}?fields=status,country,city")
            data = response.json()
            if data.get("status") == "success":
                return data.get("country"), _ascii_name(data.get("city")), "ip-api.com"
    except Exception as e:
        logger.warning(f"ip-api.com lookup failed for {ip}: {e}")

    return None, None, "unresolved"
