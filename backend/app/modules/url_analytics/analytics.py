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
    increment_clicks_batch, get_live_snapshot,
    cache_exists, get_cached_stats, set_cached_stats,
)
from redis.asyncio.lock import Lock

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

    country, city, geo_source = None, None, None
    if ip and _is_public_ip(ip):
        country, city, geo_source = await get_location(ip)

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

    summary_data, day_rows, peak_hours, by_country, by_city, by_device, by_browser = await asyncio.gather(
        repo.get_summary(code),
        repo.get_clicks_by_day(code),
        repo.get_peak_hours(code),
        repo.get_by_country(code),
        repo.get_by_city(code),
        repo.get_by_device(code),
        repo.get_by_browser(code),
    )

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
        clicks_by_day=[ClicksByDayItem(date=r["date"], clicks=r["clicks"]) for r in day_rows],
        peak_hours=peak_hours,
        by_country=sort_desc(by_country),
        by_city=sort_desc(by_city),
        by_device=sort_desc(by_device),
        by_browser=sort_desc(by_browser),
    )


async def db_unique_ips(code: str, db: AsyncSession):
    return await UrlRepository(db).get_unique_ips(code)


async def _rebuild_cache(code: str, db: AsyncSession) -> UrlStatsResponse:
    response = await db_read(code, db)
    unique_ips = await db_unique_ips(code, db)
    await set_cached_stats(code, response, unique_ips)
    return response


async def cache_stampede_guard(code: str, db: AsyncSession) -> UrlStatsResponse:
    """On a cache miss, many concurrent requests for the same `code` would
    otherwise all fall through to Postgres at once (cache stampede). A
    distributed lock ensures only one request rebuilds the cache — everyone
    else either waits for it or, once acquired, re-checks the cache first
    since another request may have just filled it."""
    lock = Lock(redis_client, f"lock:stats:{code}", timeout=10, blocking_timeout=10)

    if await lock.acquire():
        try:
            if await cache_exists(code):
                return await get_cached_stats(code)
            return await _rebuild_cache(code, db)
        finally:
            await lock.release()

    # Didn't get the lock in time — the rebuild should be done (or nearly done) by now.
    if await cache_exists(code):
        return await get_cached_stats(code)
    logger.warning(f"Cache stampede guard timed out for code={code}, falling back to direct DB read")
    return await db_read(code, db)


async def redis_cache(code: str, db: AsyncSession) -> UrlStatsResponse:
    if await cache_exists(code):
        logger.info("Successfully read URL Anlaytics from Redis for code=%s", code)
        return await get_cached_stats(code)

    return await cache_stampede_guard(code, db)


def _cap_top_n(d: dict, n: int = 20) -> dict:
    return dict(list(d.items())[:n])


async def get_url_stats(code: str, db: AsyncSession) -> UrlStatsResponse:
    response = await redis_cache(code, db)
    return response.model_copy(update={
        "by_country": _cap_top_n(response.by_country),
        "by_city": _cap_top_n(response.by_city),
        "by_browser": _cap_top_n(response.by_browser),
    })

async def run_url_analytics_redis(payloads: list[dict]) -> None:
    try:
        clicks = await asyncio.gather(*[
            parse_click_data(p["code"], _make_request(p))
            for p in payloads
        ])

        await increment_clicks_batch(clicks)

        # Multiple clicks in a batch often share a code — snapshot/publish once
        # per unique code, not once per click. Sequential on purpose: this keeps
        # Redis usage at 1 connection at a time, so it can never itself trigger
        # pool contention/errors, even at the cost of added latency under load.
        unique_codes = {c.code for c in clicks}
        for code in unique_codes:
            payload = await get_live_snapshot(code)
            await redis_client.publish(f"updates:{code}", payload.model_dump_json())

        logger.info(f"Redis: incremented counters and published updates for {len(unique_codes)} codes ({len(clicks)} click events)")

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

