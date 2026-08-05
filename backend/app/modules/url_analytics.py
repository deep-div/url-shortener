import datetime
import ipaddress
import pytz

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.schema import AnalyticsResponse, UrlStatsResponse, DashboardResponse, ClicksByDayItem, TopUrlItem, DeviceType, OsType
from app.repositories.url_repository import UrlRepository
from app.clients.postgresql import AsyncSessionLocal
from app.clients.geoip import get_location

import user_agents

IST = pytz.timezone("Asia/Kolkata")


def _is_public_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


class UrlAnalytics:

    def parse_click_data(self, code: str, request: Request) -> AnalyticsResponse:
        ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
        )
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


class UrlAnalyticsDashboard:

    async def get_url_stats(self, code: str, db: AsyncSession) -> UrlStatsResponse:
        repo = UrlRepository(db)
        return UrlStatsResponse(
            code=code,
            total_clicks=await repo.get_total_clicks(code),
            clicks_by_day=[ClicksByDayItem(**r) for r in await repo.get_clicks_by_day(code)],
            by_device=await repo.get_breakdown(code, "device"),
            by_browser=await repo.get_breakdown(code, "browser"),
            by_os=await repo.get_breakdown(code, "os"),
        )

    async def get_dashboard(self, db: AsyncSession) -> DashboardResponse:
        repo = UrlRepository(db)
        return DashboardResponse(
            total_urls=await repo.get_total_urls(),
            total_clicks=await repo.get_total_clicks_all(),
            clicks_today=await repo.get_clicks_today(),
            top_urls=[TopUrlItem(**r) for r in await repo.get_top_urls()],
        )


async def run_get_url_stats(code: str, db: AsyncSession) -> UrlStatsResponse:
    return await UrlAnalyticsDashboard().get_url_stats(code, db)


async def run_get_dashboard(db: AsyncSession) -> DashboardResponse:
    return await UrlAnalyticsDashboard().get_dashboard(db)


async def run_url_analytics(code: str, request: Request) -> None:
    """Background task — creates its own DB session, off the critical path."""
    click = UrlAnalytics().parse_click_data(code, request)
    async with AsyncSessionLocal() as db:
        await UrlRepository(db).save_analytics(click)