import datetime
import pytz

from fastapi import Request
from sqlalchemy.orm import Session

from app.modules.schema import AnalyticsResponse, UrlStatsResponse, DashboardResponse, ClicksByDayItem, TopUrlItem, DeviceType, OsType, ReferrerType
from app.repositories.url_repository import UrlRepository

import user_agents

IST = pytz.timezone("Asia/Kolkata")

class UrlAnalytics:

    def parse_click_data(self, code: str, request: Request) -> AnalyticsResponse:
        ip = request.client.host if request.client else None
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

        raw_referrer = request.headers.get("referer") or request.headers.get("referrer")
        referrer = self._parse_referrer(raw_referrer)

        return AnalyticsResponse(
            code=code,
            clicked_at=datetime.datetime.now(IST),
            ip=ip,
            device=device,
            browser=browser,
            os=os_name,
            referrer=referrer,
        )

    def _parse_referrer(self, raw: str | None) -> ReferrerType:
        if not raw:
            return ReferrerType.Direct
        raw = raw.lower()
        if "google" in raw:
            return ReferrerType.Google
        if "twitter" in raw or "t.co" in raw:
            return ReferrerType.Twitter
        if "linkedin" in raw:
            return ReferrerType.LinkedIn
        if "facebook" in raw or "fb.com" in raw:
            return ReferrerType.Facebook
        if "instagram" in raw:
            return ReferrerType.Instagram
        if "youtube" in raw:
            return ReferrerType.YouTube
        return ReferrerType.Other


class UrlAnalyticsDashboard:

    def get_url_stats(self, code: str, db: Session) -> UrlStatsResponse:
        repo = UrlRepository(db)
        return UrlStatsResponse(
            code=code,
            total_clicks=repo.get_total_clicks(code),
            unique_clicks=repo.get_unique_clicks(code),
            clicks_by_day=[ClicksByDayItem(**r) for r in repo.get_clicks_by_day(code)],
            by_device=repo.get_breakdown(code, "device"),
            by_browser=repo.get_breakdown(code, "browser"),
            by_os=repo.get_breakdown(code, "os"),
            by_referrer=repo.get_breakdown(code, "referrer"),
        )

    def get_dashboard(self, db: Session) -> DashboardResponse:
        repo = UrlRepository(db)
        return DashboardResponse(
            total_urls=repo.get_total_urls(),
            total_clicks=repo.get_total_clicks_all(),
            clicks_today=repo.get_clicks_today(),
            top_urls=[TopUrlItem(**r) for r in repo.get_top_urls()],
        )


def run_get_url_stats(code: str, db: Session) -> UrlStatsResponse:
    return UrlAnalyticsDashboard().get_url_stats(code, db)


def run_get_dashboard(db: Session) -> DashboardResponse:
    return UrlAnalyticsDashboard().get_dashboard(db)

def run_url_analytics(code: str, request: Request, db: Session) -> AnalyticsResponse:
    click = UrlAnalytics().parse_click_data(code, request)
    UrlRepository(db).save_analytics(click)
    return click