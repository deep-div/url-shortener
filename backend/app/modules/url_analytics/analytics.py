import asyncio
from types import SimpleNamespace
import datetime
import ipaddress
import pytz

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.url_analytics.schema import (
    AnalyticsResponse, UrlStatsResponse, ClicksByDayItem, ClicksByHourItem,
    LinkInfo, SummaryInfo, DeviceType,
)
from app.modules.url_analytics.repository import UrlRepository
from app.clients.postgresql import AsyncSessionLocal
# from app.clients.redis import redis_client
# from app.modules.url_analytics.counters_redis import try_claim_cold_start, populate_from_db, increment_counters, get_snapshot
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

def _group_hours_by_date(rows: list[dict]) -> list[ClicksByHourItem]:
    grouped: dict[str, dict[int, int]] = {}
    for r in rows:
        grouped.setdefault(r["date"], {})[r["hour"]] = r["clicks"]
    return [ClicksByHourItem(date=date, hours=hours) for date, hours in sorted(grouped.items())]


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
    device, browser, os_name = None, None, None

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
        os_name = ua.os.family or None
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
        os=os_name,
    )


async def get_url_stats(code: str, db: AsyncSession, from_date=None, to_date=None) -> UrlStatsResponse:
    repo = UrlRepository(db)
    url_row = await repo.get_by_code(code)
    if not url_row:
        logger.warning(f"Analytics requested for unknown code: {code}")
        raise HTTPException(status_code=404, detail="Short code not found")
    summary_data = await repo.get_summary(code, url_row.created_at)
    by_country = await repo.get_breakdown(code, "country", from_date, to_date)
    by_city = await repo.get_breakdown(code, "city", from_date, to_date)
    summary_data["total_countries"] = len(by_country)
    summary_data["total_cities"] = len(by_city)
    return UrlStatsResponse(
        link=LinkInfo(
            code=url_row.code,
            short_url=url_row.short_url,
            long_url=url_row.long_url,
            created_at=url_row.created_at,
        ),
        summary=SummaryInfo(**summary_data),
        clicks_by_day=[ClicksByDayItem(**r) for r in await repo.get_clicks_by_day(code, from_date, to_date)],
        clicks_by_hour=_group_hours_by_date(await repo.get_clicks_by_hour(code, from_date, to_date)),
        peak_hours=await repo.get_peak_hours(code, from_date, to_date),
        by_country=by_country,
        by_city=by_city,
        by_device=await repo.get_breakdown(code, "device", from_date, to_date),
        by_browser=await repo.get_breakdown(code, "browser", from_date, to_date),
        by_os=await repo.get_breakdown(code, "os", from_date, to_date),
    )


def build_live_snapshot(stats: UrlStatsResponse) -> dict:
    """Serialize a UrlStatsResponse into a JSON-safe dict for live WS push."""
    return {
        "summary": {
            "total_clicks": stats.summary.total_clicks,
            "unique_clicks": stats.summary.unique_clicks,
            "clicks_today": stats.summary.clicks_today,
            "clicks_this_week": stats.summary.clicks_this_week,
            "avg_clicks_per_day": stats.summary.avg_clicks_per_day,
            "total_countries": stats.summary.total_countries,
            "total_cities": stats.summary.total_cities,
            "last_clicked_at": stats.summary.last_clicked_at.isoformat() if stats.summary.last_clicked_at else None,
        },
        "by_country": stats.by_country,
        "by_city": stats.by_city,
        "by_device": stats.by_device,
        "by_browser": stats.by_browser,
        "by_os": stats.by_os,
    }


async def run_url_analytics_batch(payloads: list[dict]) -> None:
    """Process a batch of click events — one bulk DB insert instead of N individual ones."""
    try:
        clicks = await asyncio.gather(*[
            parse_click_data(p["code"], _make_request(p))
            for p in payloads
        ])

        async with AsyncSessionLocal() as db:
            repo = UrlRepository(db)

            # # Cold start check per unique code in this batch
            # for code in {c.code for c in clicks}:
            #     if await try_claim_cold_start(code):
            #         stats = await get_url_stats(code, db)
            #         await populate_from_db(code, stats)

            await repo.save_analytics_batch(list(clicks))
            logger.info(f"Batch inserted {len(clicks)} clicks")

        # # Increment Redis counters and publish snapshots per click
        # for click, is_unique in zip(clicks, unique_flags):
        #     await increment_counters(click.code, click, is_unique)

        # for code in {c.code for c in clicks}:
        #     snapshot = json.dumps(await get_snapshot(code))
        #     await redis_client.publish(f"analytics:{code}", snapshot)
        #     logger.info(f"Redis publish done for code: {code}")

    except Exception as e:
        logger.error(f"Batch analytics failed: {e}", exc_info=True)

