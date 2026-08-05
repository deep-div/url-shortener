import atexit
import os
from geoip2.database import Reader
from app.core.logging import logger

GEOIP_DB_PATH = "geoipdb/GeoLite2-City.mmdb"

_reader = None


def init_geoip():
    global _reader
    if not os.path.exists(GEOIP_DB_PATH):
        logger.warning(f"GeoIP database not found at {GEOIP_DB_PATH}. Geolocation will be disabled.")
        return
    try:
        _reader = Reader(GEOIP_DB_PATH)
        atexit.register(_reader.close)
        logger.info("GeoIP database loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load GeoIP database: {e}")


def get_location(ip: str) -> tuple[str | None, str | None]:
    if not _reader:
        return None, None

    try:
        response = _reader.city(ip)
        country = response.country.name
        city = response.city.name
        return country, city
    except Exception as e:
        logger.debug(f"GeoIP lookup failed for {ip}: {e}")
        return None, None
