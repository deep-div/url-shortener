import datetime
import ipaddress
import pytz

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.schema import (
    AnalyticsResponse, UrlStatsResponse, ClicksByDayItem, ClicksByHourItem,
    LinkInfo, SummaryInfo, DeviceType, OsType,
)
from app.repositories.url_repository import UrlRepository
from app.clients.postgresql import AsyncSessionLocal
from app.clients.geoip import get_location

import user_agents
from app.core.logging import logger

IST = pytz.timezone("Asia/Kolkata")


def _is_public_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def _group_hours_by_date(rows: list[dict]) -> list[ClicksByHourItem]:
    grouped: dict[str, dict[int, int]] = {}
    for r in rows:
        grouped.setdefault(r["date"], {})[r["hour"]] = r["clicks"]
    return [ClicksByHourItem(date=date, hours=hours) for date, hours in sorted(grouped.items())]


def parse_click_data(code: str, request: Request) -> AnalyticsResponse:
    ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else None)
    )
    logger.info(f"Click captured from IP: {ip}")
    country, city = None, None
    if ip and _is_public_ip(ip):
        country, city = get_location(ip)

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
        browser = ua.browser.family or None
        raw_os = ua.os.family or ""
        os_name = OsType.from_ua(raw_os) if raw_os else None

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


async def run_url_analytics(code: str, request: Request) -> None:
    """Background task — creates its own DB session, off the critical path."""
    click = parse_click_data(code, request)
    async with AsyncSessionLocal() as db:
        await UrlRepository(db).save_analytics(click)
