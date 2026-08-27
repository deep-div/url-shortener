import asyncio
from types import SimpleNamespace
import datetime
import ipaddress
import pytz

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.url_analytics.schema import (
    AnalyticsResponse, UrlStatsResponse, ClicksByDayItem,
    LinkInfo, SummaryInfo, DeviceType,
)
from app.modules.url_analytics.repository import UrlRepository
from app.modules.url_analytics.redis_counter import (
    increment_click, get_live_snapshot,
    cache_exists, get_cached_stats, set_cached_stats,
)
from app.clients.postgresql import AsyncSessionLocal
from app.clients.redis import redis_client
from app.clients.geoip import get_location

import user_agents
from app.core.logging import logger

IST = pytz.timezone("Asia/Kolkata")


def _is_public_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False

def _make_request(payload: dict):
    ip = payload.get("ip_from_headers", "")
    return SimpleNamespace(
        query_params={"ipv4": payload.get("ipv4", "")},
        headers={"x-forwarded-for": ip, "user-agent": payload.get("user_agent", "")},
        client=SimpleNamespace(host=ip),
    )


async def parse_click_data(code: str, request: Request) -> AnalyticsResponse:
    ipv4 = request.query_params.get("ipv4", "").strip()
    if ipv4 and _is_public_ip(ipv4):
        ip = ipv4
    else:  # get ipv6 if ipv4 does not comes with request 
        raw_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
        )
        ip = raw_ip

    logger.info(f"Click captured from IP: {ip} (ipv4={ipv4 or 'none'})")
    country, city, geo_source = None, None, None
    if ip and _is_public_ip(ip):
        country, city, geo_source = await get_location(ip)
    logger.info(f"Location resolved: {country}, {city} via {geo_source} for IP: {ip}")

    raw_ua = request.headers.get("user-agent", "")
    device, browser = None, None

    if raw_ua:
        ua = user_agents.parse(raw_ua)
        if ua.is_mobile:
            device = DeviceType.Mobile
        elif ua.is_tablet:
            device = DeviceType.Tablet
        elif ua.is_pc:
            device = DeviceType.Desktop
        else:
            device = DeviceType.Other
            logger.warning(f"Unrecognised user-agent for code {code}: {raw_ua[:120]}")
        browser = ua.browser.family or None
    else:
        logger.warning(f"Missing user-agent header for code: {code}")

    return AnalyticsResponse(
        code=code,
        clicked_at=datetime.datetime.now(IST),
        ip=ip,
        country=country,
        city=city,
        device=device,
        browser=browser,
    )
    
    
async def db_read(code: str, db: AsyncSession) -> UrlStatsResponse:
    """Cache-miss path — reads Postgres and builds the full UrlStatsResponse,
    which also acts as the payload used to re-seed the Redis cache."""
    repo = UrlRepository(db)
    url_row = await repo.get_by_code(code)
    if not url_row:
        logger.warning(f"Analytics requested for unknown code: {code}")
        raise HTTPException(status_code=404, detail="Short code not found")

    summary_data, rows = await asyncio.gather(
        repo.get_summary(code),
        repo.get_raw_clicks(code),
    )

    by_country: dict[str, int] = {}
    by_city: dict[str, int] = {}
    by_device: dict[str, int] = {}
    by_browser: dict[str, int] = {}
    clicks_by_day: dict[str, int] = {}
    peak_hours: dict[int, int] = {}

    for r in rows:
        date, hour = r["date"], r["hour"]

        clicks_by_day[date] = clicks_by_day.get(date, 0) + 1
        peak_hours[hour] = peak_hours.get(hour, 0) + 1

        by_country[r["country"]] = by_country.get(r["country"], 0) + 1
        by_city[r["city"]] = by_city.get(r["city"], 0) + 1
        by_device[r["device"]] = by_device.get(r["device"], 0) + 1
        by_browser[r["browser"]] = by_browser.get(r["browser"], 0) + 1

    sort_desc = lambda d: dict(sorted(d.items(), key=lambda x: -x[1]))

    return UrlStatsResponse(
        link=LinkInfo(
            code=url_row.code,
            short_url=url_row.short_url,
            long_url=url_row.long_url,
        ),
        summary=SummaryInfo(
            total_clicks=summary_data["total_clicks"],
            unique_clicks=summary_data["unique_clicks"],
            total_countries=len(by_country),
            total_cities=len(by_city),
            last_clicked_at=summary_data["last_clicked_at"],
        ),
        clicks_by_day=[ClicksByDayItem(date=d, clicks=c) for d, c in sorted(clicks_by_day.items())],
        peak_hours=peak_hours,
        by_country=sort_desc(by_country),
        by_city=sort_desc(by_city),
        by_device=sort_desc(by_device),
        by_browser=sort_desc(by_browser),
    )


async def redis_cache(code: str, db: AsyncSession) -> UrlStatsResponse:
    if await cache_exists(code):
        return await get_cached_stats(code)

    response = await db_read(code, db)
    await set_cached_stats(code, response)
    return response


async def get_url_stats(code: str, db: AsyncSession) -> UrlStatsResponse:
    return await redis_cache(code, db)

async def run_url_analytics_redis(payloads: list[dict]) -> None:
    try:
        clicks = await asyncio.gather(*[
            parse_click_data(p["code"], _make_request(p))
            for p in payloads
        ])

        await asyncio.gather(*[
            increment_click(
                code=c.code,
                clicked_at=c.clicked_at,
                country=c.country,
                city=c.city,
                device=c.device.value if c.device else None,
                browser=c.browser,
            )
            for c in clicks
        ])

        for c in clicks:
            payload = await get_live_snapshot(c.code)
            await redis_client.publish(f"updates:{c.code}", payload.model_dump_json())

        logger.info(f"Redis: incremented counters and published {len(clicks)} click events")

    except Exception as e:
        logger.error(f"Redis analytics failed: {e}", exc_info=True)
        raise

async def run_url_analytics_batch(payloads: list[dict]) -> None:
    """Process a batch of click events — one bulk DB insert instead of N individual ones."""
    try:
        clicks = await asyncio.gather(*[
            parse_click_data(p["code"], _make_request(p))
            for p in payloads
        ])

        async with AsyncSessionLocal() as db:
            repo = UrlRepository(db)

            await repo.save_analytics_batch(list(clicks))
            logger.info(f"Batch inserted {len(clicks)} clicks")

    except Exception as e:
        logger.error(f"Batch analytics failed: {e}", exc_info=True)
        raise

