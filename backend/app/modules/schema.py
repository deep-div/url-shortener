import datetime
from pydantic import BaseModel


class ShortenResponse(BaseModel):
    short_url: str
    code: str


class AnalyticsResponse(BaseModel):
    code: str
    clicked_at: datetime.datetime
    ip: str | None
    device: str | None
    browser: str | None
    os: str | None
    referrer: str | None
    country: str | None
    city: str | None

    class Config:
        from_attributes = True


class ClicksByDayItem(BaseModel):
    date: str
    clicks: int


class TopUrlItem(BaseModel):
    code: str
    clicks: int


class UrlStatsResponse(BaseModel):
    code: str
    total_clicks: int
    unique_clicks: int
    clicks_by_day: list[ClicksByDayItem]
    by_device: dict
    by_browser: dict
    by_os: dict
    by_referrer: dict
    by_country: dict


class DashboardResponse(BaseModel):
    total_urls: int
    total_clicks: int
    clicks_today: int
    top_urls: list[TopUrlItem]
